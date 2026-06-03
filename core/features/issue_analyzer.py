def issue_bucket(issue_str):
    try:
        num = int(issue_str)
    except (TypeError, ValueError):
        return "Unknown"
    if num == 1:
        return "#1"
    elif num <= 10:
        return "2-10"
    elif num <= 100:
        return "11-100"
    else:
        return ">100"
