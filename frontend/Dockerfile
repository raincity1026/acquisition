# 构建静态文件
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
# 用淘宝 npm 镜像加速国内安装
RUN npm config set registry https://registry.npmmirror.com && npm ci
COPY . .
RUN npm run build

# 用 nginx 托管 + 反代 /api
FROM nginx:1.27-alpine
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/app.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80 443
