#!/usr/bin/env python3
"""
Mini AI Benchmark for Cloudflare Workers AI
Tests various capabilities similar to GAIA benchmark
"""
import time
import json
from pathlib import Path
from examples.run_cloudflare_workers import construct_society
from owl.utils import run_society

def run_mini_benchmark():
    """Run a mini benchmark with various AI tasks"""
    
    # Test tasks covering different capabilities
    test_tasks = [
        {
            "id": "math_01",
            "question": "Calculate the compound interest on $1000 invested at 5% annual interest for 3 years. Show your work.",
            "expected_type": "numerical",
            "difficulty": 1
        },
        {
            "id": "reasoning_01", 
            "question": "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain your reasoning.",
            "expected_type": "logical",
            "difficulty": 2
        },
        {
            "id": "coding_01",
            "question": "Write a Python function that finds the second largest number in a list. Include error handling and create a test file.",
            "expected_type": "code",
            "difficulty": 2
        },
        {
            "id": "research_01",
            "question": "Search for information about renewable energy trends in 2024 and create a summary with key statistics.",
            "expected_type": "research",
            "difficulty": 3
        },
        {
            "id": "document_01",
            "question": "Create a professional business proposal document (PDF) for a solar energy consulting service, including executive summary, services, and pricing.",
            "expected_type": "document",
            "difficulty": 3
        }
    ]
    
    results = []
    
    print("🚀 Starting Mini AI Benchmark for Cloudflare Workers")
    print("=" * 60)
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n📋 Task {i}/{len(test_tasks)}: {task['id']}")
        print(f"Difficulty: {'⭐' * task['difficulty']}")
        print(f"Question: {task['question']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Create AI society and run task
            society = construct_society(task['question'])
            answer, chat_history, token_count = run_society(society)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Evaluate success (basic checks)
            success = evaluate_answer(answer, task)
            
            result = {
                "task_id": task['id'],
                "question": task['question'],
                "difficulty": task['difficulty'],
                "answer": answer,
                "success": success,
                "duration_seconds": round(duration, 2),
                "token_count": token_count,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results.append(result)
            
            # Print result
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{status} - Completed in {duration:.1f}s")
            print(f"Tokens used: {token_count}")
            print(f"Answer preview: {answer[:200]}...")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            result = {
                "task_id": task['id'],
                "question": task['question'],
                "difficulty": task['difficulty'],
                "answer": None,
                "success": False,
                "error": str(e),
                "duration_seconds": 0,
                "token_count": 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(result)
    
    # Generate summary
    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r['success'])
    total_time = sum(r['duration_seconds'] for r in results)
    total_tokens = sum(r.get('token_count', 0) for r in results)
    
    summary = {
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "success_rate": round(successful_tasks / total_tasks * 100, 1),
        "total_time_seconds": round(total_time, 2),
        "total_tokens": total_tokens,
        "average_time_per_task": round(total_time / total_tasks, 2),
        "results": results
    }
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"cloudflare_benchmark_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🏆 BENCHMARK COMPLETED")
    print("=" * 60)
    print(f"Tasks completed: {successful_tasks}/{total_tasks}")
    print(f"Success rate: {summary['success_rate']}%")
    print(f"Total time: {total_time:.1f} seconds")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Average time per task: {summary['average_time_per_task']:.1f} seconds")
    print(f"Results saved to: {results_file}")
    
    return summary

def evaluate_answer(answer, task):
    """Basic evaluation of task completion"""
    if not answer or len(answer.strip()) < 50:
        return False
    
    answer_lower = answer.lower()
    
    # Basic checks based on task type
    if task['expected_type'] == 'numerical':
        # Check for numbers and mathematical terms
        return any(word in answer_lower for word in ['$', 'interest', 'calculate', '%']) and \
               any(char.isdigit() for char in answer)
    
    elif task['expected_type'] == 'logical':
        # Check for reasoning terms
        return any(word in answer_lower for word in ['therefore', 'because', 'reasoning', 'conclude', 'logic'])
    
    elif task['expected_type'] == 'code':
        # Check for code-related content
        return any(word in answer_lower for word in ['def ', 'function', 'python', 'return', 'list'])
    
    elif task['expected_type'] == 'research':
        # Check for research indicators
        return any(word in answer_lower for word in ['2024', 'trends', 'statistics', 'energy', 'renewable'])
    
    elif task['expected_type'] == 'document':
        # Check for document creation
        return any(word in answer_lower for word in ['document', 'pdf', 'proposal', 'business', 'executive'])
    
    return True  # Default to success if basic length check passes

if __name__ == "__main__":
    run_mini_benchmark()