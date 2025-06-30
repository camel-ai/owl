#!/usr/bin/env python3
"""
Simple interactive script to use Cloudflare Workers AI
"""
from examples.run_cloudflare_workers import construct_society
from owl.utils import run_society

def main():
    # Get user input
    question = input("Enter your question: ")
    
    print("Creating AI society with Cloudflare Workers AI...")
    society = construct_society(question)
    
    print("Running conversation...")
    answer, chat_history, token_count = run_society(society)
    
    print("\n" + "="*50)
    print("FINAL ANSWER:")
    print("="*50)
    print(answer)
    print("\n" + "="*50)
    print(f"Token count: {token_count}")

if __name__ == "__main__":
    main()