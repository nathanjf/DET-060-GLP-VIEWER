from app import create_app
from app import sched

app = create_app()

if __name__ == "__main__":
    app.run()