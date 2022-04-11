import sqlite3


class tbwdb:
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def blocks(self):
        return self.cursor.execute(f"SELECT * FROM blocks")

    def last_block_heigh(self):
        return self.cursor.execute(
            f"SELECT height FROM blocks ORDER BY height DESC LIMIT 1"
        )

    def pending_voters_payout(self):
        return self.cursor.execute(f"SELECT sum(u_balance) FROM voters")

    def pending_delegate_payout(self):
        return self.cursor.execute(f"SELECT sum(u_balance) FROM delegate_rewards")

    def staged_payout(self):
        return self.cursor.execute(
            f"SELECT sum(payamt) FROM staging WHERE processed_at IS NULL"
        )

    def processed_transactions(self, last="100"):
        return self.cursor.execute(
            f"SELECT address,amount,processed_at FROM transactions ORDER BY processed_at DESC LIMIT {last}"
        )

    def delegate_total_rewards(self):
        return self.cursor.execute(
            f"SELECT SUM(amount) FROM transactions INNER JOIN delegate_rewards ON delegate_rewards.address = transactions.address"
        )

    def voters_total_rewards(self):
        return self.cursor.execute(
            "SELECT SUM(amount) FROM transactions INNER JOIN delegate_rewards ON delegate_rewards.address != transactions.address"
        )
