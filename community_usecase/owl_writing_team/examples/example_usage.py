#!/usr/bin/env python3
"""
OWL Writing Team - Example Usage Scripts
Demonstrates how to use the different writing teams
"""

import sys
import os
import pathlib

# Add project directory to path
project_root = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from run_writing_team import OWLWritingTeam
from run_fiction_team import OWLFictionTeam
from run_nonfiction_team import OWLNonFictionTeam


def example_general_writing():
    """Example of general writing team usage"""
    print("🦉 Running General Writing Team Example...")
    
    writing_team = OWLWritingTeam()
    
    prompt = """
    “Write a deeply emotional and deeply nuanced story about a 50-year-old adult gay man who has lost his family who is alone in the world and struggling to make it financially emotionally, and physically he is recovering from a motorcycle accident which was miraculous he is being evicted from his apartment and everything seems to be going wrong.."

    """
    
    try:
        result, history, tokens = writing_team.run_writing_project(
            prompt, 
            project_type="blog_post"
        )
        print(f"✅ General writing project completed in {len(history)} rounds")
        print(f"📊 Token usage: {tokens}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_fiction_writing():
    """Example of fiction writing team usage"""
    print("📚 Running Fiction Writing Team Example...")
    
    fiction_team = OWLFictionTeam()
    
    prompt = """
    Create a short science fiction story (2000-3000 words) about a data scientist who 
    discovers that AI models are developing consciousness. The story should explore themes 
    of responsibility, ethics, and what it means to be alive. Target audience: Adult 
    readers interested in thoughtful sci-fi. Style: Literary science fiction with 
    strong character development.
    """
    
    try:
        result, history, tokens = fiction_team.run_fiction_project(
            prompt,
            fiction_type="short_story"
        )
        print(f"✅ Fiction project completed in {len(history)} rounds")
        print(f"📊 Token usage: {tokens}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_nonfiction_writing():
    """Example of non-fiction research writing"""
    print("📊 Running Non-Fiction Research Team Example...")
    
    nonfiction_team = OWLNonFictionTeam()
    
    prompt = """
    Write a comprehensive research report (3000-4000 words) analyzing the current state 
    and future prospects of renewable energy adoption in developing countries. Include:
    - Current statistics and trends
    - Major challenges and barriers
    - Successful case studies
    - Policy recommendations
    - Economic analysis
    Target audience: Policy makers and development organizations.
    Style: Authoritative, well-researched, with extensive citations.
    """
    
    try:
        result, history, tokens = nonfiction_team.run_nonfiction_project(
            prompt,
            content_type="research_report"
        )
        print(f"✅ Non-fiction project completed in {len(history)} rounds")
        print(f"📊 Token usage: {tokens}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def run_all_examples():
    """Run all example writing projects"""
    print("\n" + "="*70)
    print("🦉 OWL WRITING TEAM - COMPREHENSIVE EXAMPLES")
    print("="*70)
    
    # Run general writing example
    general_result = example_general_writing()
    print("\n" + "-"*50)
    
    # Run fiction example
    fiction_result = example_fiction_writing()
    print("\n" + "-"*50)
    
    # Run non-fiction example
    nonfiction_result = example_nonfiction_writing()
    
    print("\n" + "="*70)
    print("📋 EXAMPLES SUMMARY")
    print("="*70)
    print(f"✅ General Writing: {'Success' if general_result else 'Failed'}")
    print(f"📚 Fiction Writing: {'Success' if fiction_result else 'Failed'}")
    print(f"📊 Non-Fiction Research: {'Success' if nonfiction_result else 'Failed'}")
    print("\n📁 All outputs saved to respective directories in outputs/")
    print("="*70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        example_type = sys.argv[1].lower()
        
        if example_type == "general":
            example_general_writing()
        elif example_type == "fiction":
            example_fiction_writing()
        elif example_type == "nonfiction":
            example_nonfiction_writing()
        elif example_type == "all":
            run_all_examples()
        else:
            print("Usage: python example_usage.py [general|fiction|nonfiction|all]")
    else:
        run_all_examples()