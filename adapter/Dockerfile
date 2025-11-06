FROM node:18-alpine

# Install ffmpeg for audio compression
RUN apk add --no-cache ffmpeg

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5005

# Start the application
CMD ["node", "xiaozhi-adapter.js"]
