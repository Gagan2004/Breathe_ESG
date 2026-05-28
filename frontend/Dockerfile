# Build Stage
FROM node:22-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build production assets
RUN npm run build

# Serve Stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
# Custom nginx conf to support React Router fallback if needed (though we use tab-based, it's good practice)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
