# Use the official Apify Playwright image (includes pre-configured browsers)
FROM apify/actor-node-playwright-chrome:20

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install packages without installing development tools
RUN npm --quiet set progress=false \
    && npm install --only=prod --no-audit

# Copy the rest of your scraper source code
COPY . ./

# This is the command that starts your scraper
CMD ["npm", "start"]