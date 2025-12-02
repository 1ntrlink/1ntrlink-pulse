# first line: 18
@memory.cache(ignore=['session'])  # Cache this function's results
def fetch_transactions(session, start_date, end_date):
    all_transactions = []
    current_start = start_date
    while current_start < end_date:
        chunk_end = min(current_start + timedelta(days=7), end_date)
        chunk_start_ms = int(current_start.timestamp() * 1000)
        chunk_end_ms = int(chunk_end.timestamp() * 1000)

        cursor = None
        while True:
            params = {
                'accountType': 'UNIFIED',
                'category': 'linear',
                'currency': 'USDT',
                'startTime': chunk_start_ms,
                'endTime': chunk_end_ms,
                'limit': 50
            }
            if cursor:
                params['cursor'] = cursor

            try:
                response = session.get_transaction_log(**params)
            except Exception as e:
                time.sleep(5)
                continue

            if response['retCode'] != 0 or not response['result']['list']:
                break

            all_transactions.extend(response['result']['list'])
            cursor = response['result'].get('nextPageCursor')
            if not cursor:
                break
            time.sleep(0.2)  # Reduced sleep for faster fetch, still safe

        current_start = chunk_end

    return all_transactions
