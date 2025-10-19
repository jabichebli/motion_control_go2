from utils.logger import RunLogger

logger = RunLogger()
dirs = logger.get_dirs()

logger.log("Initializing PPO training...")