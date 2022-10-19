from requests import Session
from requests_futures.sessions import FuturesSession
from deploy import argo

image = "lukeraphael/minifab:server"
mount_path = "/minifab/"

session = Session()
token = "Bearer 2764ff3c24659a11cf79a3fb128221abcf11ff4f2ab0a58620793bc27689d7513d9dd12ee3e5f49f836a52ff3c3c1197b6d5001c7434222f300ad091986d2b05"


for i in range(20):
    argo.submit_json(
        "minifab",
        "argo-pv-volume",
        "argo-pv-claim",
        image,
        "/minifab/",
        ["python3", "./main.py", "--port", "7000"],
        "argo",
        token,
        session
    )