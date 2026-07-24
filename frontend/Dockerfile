# frontend/Dockerfile
FROM node:24-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN npm i -g serve@14.2.3 --no-audit --no-fund
COPY dist ./dist
RUN addgroup -S appuser && adduser -S appuser -G appuser && \
    chown -R appuser:appuser /app
USER appuser
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
