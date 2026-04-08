# XueTa

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
npm run test:unit
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

学塔
logo 来自Lucide 的layers 图标

header.vue v-for
footer.vue 通过Props向logo.vue传递颜色参数，来修改logo的颜色（colorSVG，colorText）
footer.vue 使用v-for 便于处理响应式数据

app.vue 使用路由元信息 处理在登录注册界面不使用header footer
app.vue 使用可选链控制符  ?.
        可选链的工作原理：

        如果 route.meta 存在，继续访问 route.meta.showHeaderFooter

        如果 route.meta 是 null 或 undefined，整个表达式返回 undefined

        不会抛出 Cannot read property 'showHeaderFooter' of undefined 错误

button.vue 使用props + 插槽 