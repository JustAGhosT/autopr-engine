issue_ids = [
    int(issue["id"])
    for issue in issues
    if isinstance(
        issue.get("id"),
        int | str,
    )
]