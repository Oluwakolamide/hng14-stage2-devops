# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder
WORKDIR /build
COPY package.json ./
RUN npm install --only=production

FROM node:20-alpine
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /build/node_modules ./node_modules
COPY app.js .
COPY views/ ./views/
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health \
    || exit 1
CMD ["node", "app.js"]
