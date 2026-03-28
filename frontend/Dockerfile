FROM node:24-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

RUN chown appuser:appgroup /app

USER appuser

COPY --chown=appuser:appgroup package*.json ./
RUN npm install

COPY --chown=appuser:appgroup . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
