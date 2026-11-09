// @ts-check
import prettier from 'eslint-config-prettier'
import withNuxt from './.nuxt/eslint.config.mjs'

/* `prettier` must stay last: it turns off the formatting rules that would
   fight with Prettier. */
export default withNuxt(prettier, {
  name: 'flyana/overrides',
  rules: {
    /* Redundant with TypeScript optional props, which rely on `undefined` */
    'vue/require-default-prop': 'off',
  },
})
