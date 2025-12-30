"""
Scheduler Module
Runs the LinkedIn AI/ML Auto-Poster Agent on a schedule
"""

import schedule
import time
import logging
from agent import LinkedInAIAgent
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_agent():
    """Run the agent and handle any errors"""
    try:
        logger.info("="*80)
        logger.info("Scheduled run started")
        logger.info("="*80)
        
        agent = LinkedInAIAgent()
        success = agent.run(dry_run=False)
        
        if success:
            logger.info("✅ Scheduled run completed successfully")
        else:
            logger.error("❌ Scheduled run failed")
        
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error in scheduled run: {e}", exc_info=True)


def main():
    """Main scheduler function"""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description='Schedule LinkedIn AI/ML Auto-Poster')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once immediately instead of scheduling'
    )
    
    args = parser.parse_args()
    
    # Load config to get schedule settings
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return
    
    schedule_config = config.get('schedule', {})
    
    if args.once:
        # Run once immediately
        logger.info("Running agent once (not scheduling)")
        run_agent()
        return
    
    if not schedule_config.get('enabled', True):
        logger.info("Scheduling is disabled in config. Exiting.")
        return
    
    # Set up schedule based on config
    frequency = schedule_config.get('frequency', 'daily')
    time_str = schedule_config.get('time', '09:00')
    
    if frequency == 'daily':
        schedule.every().day.at(time_str).do(run_agent)
        logger.info(f"Scheduled to run daily at {time_str}")
    elif frequency == 'weekly':
        schedule.every().week.at(time_str).do(run_agent)
        logger.info(f"Scheduled to run weekly at {time_str}")
    else:
        # Custom cron-like schedule (e.g., "monday", "wednesday", "friday")
        days = frequency.split(',')
        for day in days:
            day = day.strip().lower()
            if day == 'monday':
                schedule.every().monday.at(time_str).do(run_agent)
            elif day == 'tuesday':
                schedule.every().tuesday.at(time_str).do(run_agent)
            elif day == 'wednesday':
                schedule.every().wednesday.at(time_str).do(run_agent)
            elif day == 'thursday':
                schedule.every().thursday.at(time_str).do(run_agent)
            elif day == 'friday':
                schedule.every().friday.at(time_str).do(run_agent)
            elif day == 'saturday':
                schedule.every().saturday.at(time_str).do(run_agent)
            elif day == 'sunday':
                schedule.every().sunday.at(time_str).do(run_agent)
        logger.info(f"Scheduled to run on {frequency} at {time_str}")
    
    # Run initial check
    logger.info("Scheduler started. Waiting for scheduled time...")
    logger.info("Press Ctrl+C to stop")
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    main()

