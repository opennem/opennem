def wem_demand_all(region="wa"):
    __query = """
        select
            time_bucket_gapfill(bs.trading_interval,
            round(wbs.price, 2),
            round(wbs.generation_total, 2)
        from balancing_summary bs
        where bs.network_id='WEM'
        order by 1 desc
    """

    query = __query.format()

    return query
