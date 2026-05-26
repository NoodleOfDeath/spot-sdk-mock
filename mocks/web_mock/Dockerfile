FROM node:20-slim AS build
WORKDIR /app
COPY package.json /app/
RUN npm install --no-audit --no-fund
COPY tsconfig.json vite.config.ts index.html /app/
COPY src /app/src
COPY public /app/public
ARG VITE_API_BASE=http://localhost:3001
ARG VITE_GITHUB_URL=https://github.com/noodleofdeath/spot-sdk-mock
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_GITHUB_URL=$VITE_GITHUB_URL
RUN npx tsc --noEmit && npx vite build

FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=build /app/package.json /app/
COPY --from=build /app/node_modules /app/node_modules
COPY --from=build /app/dist /app/dist
COPY --from=build /app/vite.config.ts /app/index.html /app/
EXPOSE 4000
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "4000"]
