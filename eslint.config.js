const globals = require("globals");
const js = require("@eslint/js");
const html = require("eslint-plugin-html");

module.exports = [
  {
    files: ["eslint.config.js"],
    languageOptions: {
      globals: {
        ...globals.node
      }
    }
  },
  js.configs.recommended,
  {
    files: ["**/*.js", "**/*.html"],
    plugins: {
      html: html,
    },
    languageOptions: {
      globals: {
        ...globals.browser
      },
      ecmaVersion: 'latest',
      sourceType: 'module',
    },
    rules: {
    }
  }
];