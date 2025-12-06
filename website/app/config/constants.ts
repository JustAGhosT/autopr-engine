/**
 * Application constants
 * 
 * Centralized configuration for URLs and other constants used across the website.
 */

/**
 * The deployed AutoPR Engine application URL.
 * This is the Azure Container Apps URL where the engine is deployed.
 * 
 * Note: Once a custom domain (app.autopr.io) is configured, update this constant.
 */
export const APP_URL = 'https://prod-autopr-san-app.bravewave-1f1ec0f2.eastus2.azurecontainerapps.io';

/**
 * API base URL for AutoPR Engine
 */
export const API_URL = `${APP_URL}/api`;
