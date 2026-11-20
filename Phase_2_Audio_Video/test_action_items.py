from nlp_engine import MeetingAnalyzer


def test_extracts_specific_action_items_and_ignores_discussion_noise():
    transcript = """
    Today I want to discuss our project progress, decisions, and deadlines.
    The main goal is to make sure everyone understands their responsibilities.
    We need to focus on improving the existing features and checking whether
    everything is working correctly.
    We also need to test the complete workflow.
    First, we need to make sure all meeting details are captured correctly.
    Second, when someone speaks, the system should identify what they said.
    And third, we need to verify that summaries, decisions, and action items
    are accurate.
    We will complete summary and decision verification by 21 November.
    The action item verification should be completed by 23 November.
    Task assignment and task management testing should be completed by 25 November.
    nd decisions, when the action items starts because I'm in time they'd like.
    Now, let's discuss the action items.
    1. Check whether the meeting summary is correct. Deadline: 21 November 2026.
    2. Verify all the decisions made during the meeting. Deadline: 21 November 2026.
    3. Check whether the action items are identified correctly. Deadline: 23 November 2026.
    4. Verify that each task is assigned to the correct person. Deadline: 24 November 2026.
    5. Check whether task updates are properly reflected in the task management section.
       Deadline: 26 November 2026.
    Now, let's discuss the overall timeline.
    We will complete the summary and decision verification by 21 November.
    The action item verification should be completed by 23 November.
    Task assignment and task management testing should be completed by 25 November.
    Finally, we will test the complete workflow on 27 November 2026.
    If anyone faces a technical issue, please communicate it early.
    Before closing, remember the assigned tasks and deadlines.
    """
    analyzer = MeetingAnalyzer()

    tasks = analyzer._extract_tasks(transcript, {}, analyzer.nlp(transcript))

    assert len(tasks) == 5
    assert any("meeting summary" in task["task"].lower() for task in tasks)
    assert any("task management section" in task["task"].lower() for task in tasks)
    assert all("action items starts" not in task["task"].lower() for task in tasks)
    assert [task["deadline"] for task in tasks] == [
        "21 November 2026",
        "21 November 2026",
        "23 November 2026",
        "24 November 2026",
        "26 November 2026",
    ]


def test_keeps_clear_named_commitments_and_requests():
    transcript = """
    Maria: I'll prepare the test plan by Friday.
    Alex, please review the plan before the next meeting.
    """
    analyzer = MeetingAnalyzer()

    tasks = analyzer._extract_tasks(
        transcript,
        {"Maria": [], "Alex": []},
        analyzer.nlp(transcript),
    )

    assert len(tasks) == 2
    assert tasks[0]["assignee"] == "Maria"
    assert tasks[1]["assignee"] == "Alex"
