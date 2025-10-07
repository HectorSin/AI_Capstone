"""
DAG 테스트 및 검증 스크립트

이 스크립트는 생성된 DAG들을 테스트하고 검증합니다.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Airflow 모듈 임포트
from airflow import DAG
from airflow.models import DagBag
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('/opt/airflow/ai_modules')

class TestDAGs(unittest.TestCase):
    """DAG 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.dag_bag = DagBag()
        self.test_dag_ids = [
            'ai_podcast_generation',
            'url_analysis_dag',
            'topic_generation_dag',
            'script_generation_dag',
            'audio_generation_dag',
            'full_pipeline_dag',
            'ai_podcast_monitoring'
        ]
    
    def test_dag_import(self):
        """DAG 임포트 테스트"""
        print("DAG 임포트 테스트 시작...")
        
        # DAG 파일들이 제대로 임포트되는지 확인
        for dag_id in self.test_dag_ids:
            with self.subTest(dag_id=dag_id):
                self.assertIn(dag_id, self.dag_bag.dags)
                print(f"✓ {dag_id} DAG 임포트 성공")
    
    def test_dag_structure(self):
        """DAG 구조 테스트"""
        print("DAG 구조 테스트 시작...")
        
        for dag_id in self.test_dag_ids:
            with self.subTest(dag_id=dag_id):
                dag = self.dag_bag.get_dag(dag_id)
                self.assertIsNotNone(dag)
                
                # DAG 기본 속성 확인
                self.assertIsInstance(dag, DAG)
                self.assertEqual(dag.dag_id, dag_id)
                self.assertIsNotNone(dag.description)
                self.assertIsNotNone(dag.tags)
                
                # Task 개수 확인
                task_count = len(dag.tasks)
                self.assertGreater(task_count, 0, f"{dag_id}에 Task가 없습니다")
                
                print(f"✓ {dag_id} DAG 구조 검증 완료 ({task_count}개 Task)")
    
    def test_dag_dependencies(self):
        """DAG 의존성 테스트"""
        print("DAG 의존성 테스트 시작...")
        
        for dag_id in self.test_dag_ids:
            with self.subTest(dag_id=dag_id):
                dag = self.dag_bag.get_dag(dag_id)
                
                # Task 의존성 확인
                for task in dag.tasks:
                    # Task가 다른 Task에 의존하는지 확인
                    upstream_tasks = task.upstream_task_ids
                    downstream_tasks = task.downstream_task_ids
                    
                    # 순환 의존성 확인
                    self.assertNotIn(task.task_id, upstream_tasks, 
                                   f"{dag_id}.{task.task_id}에 순환 의존성이 있습니다")
                
                print(f"✓ {dag_id} DAG 의존성 검증 완료")
    
    def test_dag_configuration(self):
        """DAG 설정 테스트"""
        print("DAG 설정 테스트 시작...")
        
        for dag_id in self.test_dag_ids:
            with self.subTest(dag_id=dag_id):
                dag = self.dag_bag.get_dag(dag_id)
                
                # 기본 설정 확인
                self.assertIsNotNone(dag.default_args)
                self.assertIn('owner', dag.default_args)
                self.assertIn('retries', dag.default_args)
                self.assertIn('retry_delay', dag.default_args)
                
                # 스케줄 설정 확인
                if dag.schedule_interval is not None:
                    self.assertIsInstance(dag.schedule_interval, (str, timedelta))
                
                print(f"✓ {dag_id} DAG 설정 검증 완료")
    
    def test_task_operators(self):
        """Task 연산자 테스트"""
        print("Task 연산자 테스트 시작...")
        
        for dag_id in self.test_dag_ids:
            with self.subTest(dag_id=dag_id):
                dag = self.dag_bag.get_dag(dag_id)
                
                for task in dag.tasks:
                    # Task 연산자 타입 확인
                    self.assertIsNotNone(task.task_type)
                    
                    # PythonOperator인 경우 callable 확인
                    if hasattr(task, 'python_callable'):
                        self.assertIsNotNone(task.python_callable)
                
                print(f"✓ {dag_id} Task 연산자 검증 완료")
    
    def test_dag_validation(self):
        """DAG 유효성 검증"""
        print("DAG 유효성 검증 시작...")
        
        # DAG Bag 유효성 검증
        self.assertEqual(len(self.dag_bag.import_errors), 0, 
                        f"DAG 임포트 오류: {self.dag_bag.import_errors}")
        
        # 각 DAG 유효성 검증
        for dag_id in self.test_dag_ids:
            with self.subTest(dag_id=dag_id):
                dag = self.dag_bag.get_dag(dag_id)
                
                # DAG 유효성 검증
                dag.validate()
                
                print(f"✓ {dag_id} DAG 유효성 검증 완료")
    
    def test_dag_performance(self):
        """DAG 성능 테스트"""
        print("DAG 성능 테스트 시작...")
        
        for dag_id in self.test_dag_ids:
            with self.subTest(dag_id=dag_id):
                dag = self.dag_bag.get_dag(dag_id)
                
                # Task 개수 확인
                task_count = len(dag.tasks)
                self.assertLess(task_count, 50, f"{dag_id}에 Task가 너무 많습니다 ({task_count}개)")
                
                # 복잡도 확인 (간단한 휴리스틱)
                complexity_score = 0
                for task in dag.tasks:
                    complexity_score += len(task.upstream_task_ids) + len(task.downstream_task_ids)
                
                self.assertLess(complexity_score, 100, f"{dag_id}의 복잡도가 높습니다 ({complexity_score})")
                
                print(f"✓ {dag_id} DAG 성능 검증 완료 (Task: {task_count}개, 복잡도: {complexity_score})")

def run_dag_validation():
    """DAG 검증 실행"""
    print("=" * 60)
    print("AI 팟캐스트 DAG 검증 시작")
    print("=" * 60)
    
    # DAG Bag 생성
    dag_bag = DagBag()
    
    # 검증 결과
    validation_results = {
        'total_dags': len(dag_bag.dags),
        'import_errors': len(dag_bag.import_errors),
        'validation_errors': [],
        'warnings': []
    }
    
    # 임포트 오류 확인
    if dag_bag.import_errors:
        print("❌ DAG 임포트 오류:")
        for dag_id, error in dag_bag.import_errors.items():
            print(f"  - {dag_id}: {error}")
            validation_results['validation_errors'].append(f"임포트 오류: {dag_id}")
    
    # 각 DAG 검증
    for dag_id, dag in dag_bag.dags.items():
        print(f"\\n검증 중: {dag_id}")
        
        try:
            # DAG 유효성 검증
            dag.validate()
            print(f"✓ {dag_id} 검증 완료")
            
            # Task 개수 확인
            task_count = len(dag.tasks)
            if task_count > 20:
                validation_results['warnings'].append(f"{dag_id}: Task 개수가 많음 ({task_count}개)")
            
        except Exception as e:
            print(f"❌ {dag_id} 검증 실패: {e}")
            validation_results['validation_errors'].append(f"검증 실패: {dag_id} - {e}")
    
    # 결과 출력
    print("\\n" + "=" * 60)
    print("DAG 검증 결과")
    print("=" * 60)
    print(f"총 DAG 수: {validation_results['total_dags']}")
    print(f"임포트 오류: {validation_results['import_errors']}")
    print(f"검증 오류: {len(validation_results['validation_errors'])}")
    print(f"경고: {len(validation_results['warnings'])}")
    
    if validation_results['validation_errors']:
        print("\\n검증 오류:")
        for error in validation_results['validation_errors']:
            print(f"  - {error}")
    
    if validation_results['warnings']:
        print("\\n경고:")
        for warning in validation_results['warnings']:
            print(f"  - {warning}")
    
    if validation_results['import_errors'] == 0 and len(validation_results['validation_errors']) == 0:
        print("\\n🎉 모든 DAG 검증 통과!")
        return True
    else:
        print("\\n❌ 일부 DAG 검증 실패")
        return False

def test_dag_execution():
    """DAG 실행 테스트"""
    print("\\n" + "=" * 60)
    print("DAG 실행 테스트")
    print("=" * 60)
    
    # 테스트용 DAG 실행 설정
    test_config = {
        'category': 'GOOGLE',
        'host1_name': '김테크',
        'host2_name': '박AI',
        'search_recency': 'week',
        'include_audio': False
    }
    
    print(f"테스트 설정: {test_config}")
    print("\\nDAG 실행 테스트는 Airflow UI에서 수동으로 실행하세요.")
    print("1. Airflow UI 접속")
    print("2. DAG 목록에서 원하는 DAG 선택")
    print("3. 'Trigger DAG' 버튼 클릭")
    print("4. Configuration에 다음 JSON 입력:")
    print(f"   {test_config}")
    print("5. 'Trigger' 버튼 클릭")

if __name__ == '__main__':
    # DAG 검증 실행
    validation_success = run_dag_validation()
    
    # DAG 실행 테스트 안내
    test_dag_execution()
    
    # 테스트 실행
    if validation_success:
        print("\\n" + "=" * 60)
        print("단위 테스트 실행")
        print("=" * 60)
        
        # 테스트 실행
        unittest.main(argv=[''], exit=False, verbosity=2)
    else:
        print("\\n❌ DAG 검증 실패로 인해 단위 테스트를 건너뜁니다.")
        sys.exit(1)
