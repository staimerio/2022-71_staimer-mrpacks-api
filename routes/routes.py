# Retic
from retic import Router

# Controllers
import controllers.mrpacks as mrpacks

router = Router()

# Anime
router.post("/posts", mrpacks.publish_latest)