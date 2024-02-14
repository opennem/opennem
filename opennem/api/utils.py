from sqlalchemy import func


def get_query_count(query, session):
    """Get a count of all records in a query"""
    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    count = session.execute(count_q).scalar()
    return count
