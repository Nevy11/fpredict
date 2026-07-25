import io
import logging
import pandas as pd
from curl_cffi import requests

# Set up logging for validation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_managers_on_startup(repository):
    logger.info("Running manager validation check against Wikipedia...")
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_current_Premier_League_and_English_Football_League_managers'
        r = requests.get(url, impersonate='chrome', timeout=15)
        r.raise_for_status()
        
        # Suppress the FutureWarning from pandas regarding literal html strings
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=FutureWarning)
            df_list = pd.read_html(io.StringIO(r.text))
            
        if not df_list:
            logger.warning("No tables found on Wikipedia page. Skipping manager validation.")
            return

        df = df_list[0]
        if 'Division' in df.columns:
            pl_df = df[df['Division'] == 'Premier League']
        else:
            pl_df = df

        wiki_managers = {}
        for _, row in pl_df.iterrows():
            club = str(row.get('Club', '')).strip()
            manager = str(row.get('Manager', '')).strip()
            # Clean up footnote references like "Mikel Arteta[4]"
            if '[' in manager:
                manager = manager.split('[')[0].strip()
            if club and manager:
                wiki_managers[club] = manager

        for club, wiki_mgr in wiki_managers.items():
            try:
                # resolve_manager uses the TEAM_NAME_MAPPING internally if we pass it, 
                # but let's just pass the club name as is (repository matches it up)
                from src.api.main import TEAM_NAME_MAPPING
                db_club = TEAM_NAME_MAPPING.get(club, club)
                db_manager_info = repository.resolve_manager(db_club)
                if db_manager_info:
                    db_mgr = db_manager_info.get("name")
                    if db_mgr and db_mgr != wiki_mgr:
                        logger.info(f"Manager update needed for {club}: '{db_mgr}' -> '{wiki_mgr}'. Updating database...")
                        repository.update_current_manager(db_club, wiki_mgr)
                        logger.info(f"Successfully updated manager for {club} to '{wiki_mgr}'.")
            except Exception as inner_e:
                logger.debug(f"Could not resolve manager for {club}: {inner_e}")
                
        logger.info("Manager validation check completed successfully.")
    except Exception as e:
        logger.warning(f"Manager validation check failed or is offline: {e}. Skipping validation.")
