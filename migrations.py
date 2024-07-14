# the migration file is where you build your database tables
# If you create a new release for your extension , remeember the migration file is like a blockchain, never edit only add!


async def m001_initial(db):
    """
    Initial templates table.
    """
    await db.execute(
        """
        CREATE TABLE eightball.maintable (
            id TEXT PRIMARY KEY,
            wallet TEXT NOT NULL,
            name TEXT NOT NULL,
            wordlist TEXT NOT NULL,
            lnurlpayamount INTEGER DEFAULT 0,
            lnurlpay TEXT
        );
    """
    )