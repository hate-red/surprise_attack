from fastapi import FastAPI


app = FastAPI(title='Hackathon API')


@app.get('/')
async def root() -> dict:
    return {'message': 'hi there!'}
