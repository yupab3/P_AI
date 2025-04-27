#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta, timezone

from kubernetes import client, config
from kubernetes.client.rest import ApiException

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def load_k8s_config():
    """
    클러스터 내부에서 실행 중이면 in-cluster 설정,
    외부에서 실행 중이면 kubeconfig 로드
    """
    try:
        config.load_incluster_config()
        logging.info("Loaded in-cluster Kubernetes configuration")
    except config.ConfigException:
        config.load_kube_config()
        logging.info("Loaded local kubeconfig")

def delete_unused_pods(namespaces=None, threshold_hours=24):
    """
    최근 threshold_hours 시간 내 이벤트가 없는 파드를 찾아 삭제
    :param namespaces: 검사할 네임스페이스 리스트 (None 이면 모든 네임스페이스)
    :param threshold_hours: 이벤트 기준 시간(기본 24시간)
    """
    v1 = client.CoreV1Api()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)

    # 네임스페이스 목록 확보
    if namespaces is None:
        ns_list = [ns.metadata.name for ns in v1.list_namespace().items]
    else:
        ns_list = namespaces

    # 시스템 네임스페이스는 건너뛰기
    skip_ns = {"kube-system", "kube-public", "kube-node-lease"}

    for ns in ns_list:
        if ns in skip_ns:
            continue

        logging.info(f"Scanning namespace: {ns}")
        try:
            pods = v1.list_namespaced_pod(namespace=ns).items
        except ApiException as e:
            logging.error(f"Failed to list pods in {ns}: {e}")
            continue

        for pod in pods:
            pod_name = pod.metadata.name

            # 해당 파드에 연관된 이벤트 조회
            try:
                evts = v1.list_namespaced_event(
                    namespace=ns,
                    field_selector=(
                        f"involvedObject.kind=Pod,"
                        f"involvedObject.name={pod_name}"
                    )
                ).items
            except ApiException as e:
                logging.error(f"Failed to list events for pod {pod_name} in {ns}: {e}")
                continue

            # 최근 threshold_hours 시간 이내의 이벤트가 있는지 검사
            recent_events = []
            for evt in evts:
                # event_time 필드가 있으면 사용, 없으면 last_timestamp 사용
                evt_time = getattr(evt, 'event_time', None) or getattr(evt, 'last_timestamp', None)
                if evt_time and evt_time.replace(tzinfo=timezone.utc) >= cutoff:
                    recent_events.append(evt_time)

            if not recent_events:
                # 삭제 대상
                logging.info(f"Deleting pod '{pod_name}' in namespace '{ns}' (no events in last {threshold_hours}h)")
                try:
                    v1.delete_namespaced_pod(name=pod_name, namespace=ns)
                except ApiException as e:
                    logging.error(f"Failed to delete pod {pod_name} in {ns}: {e}")

def main():
    load_k8s_config()
    # 검사할 네임스페이스를 제한하려면 아래처럼 리스트 지정
    # target_namespaces = ["default", "my-app-namespace"]
    target_namespaces = None
    delete_unused_pods(namespaces=target_namespaces, threshold_hours=24)

if __name__ == "__main__":
    main()
