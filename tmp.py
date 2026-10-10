import asyncio
from app.database import async_session_maker
from app.seed import main
asyncio.run(main())
