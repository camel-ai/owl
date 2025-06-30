#!/usr/bin/env python3
"""
Custom script using Cloudflare Workers AI
"""
from examples.run_cloudflare_workers import construct_society
from owl.utils import run_society

# Your questions
questions = [
    "What is machine learning?",
    "Write a Python function to reverse a string",
    "Explain quantum computing in simple terms"
]

for i, question in enumerate(questions, 1):
    print(f"\n{'='*60}")
    print(f"QUESTION {i}: {question}")
    print('='*60)
    
    society = construct_society(question)
    answer, _, token_count = run_society(society)
    
    print(f"ANSWER: {answer}")
    print(f"Tokens used: {token_count}")
    print('='*60)