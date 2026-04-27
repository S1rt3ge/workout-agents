import js from "@eslint/js"
import reactHooks from "eslint-plugin-react-hooks"
import tseslint from "typescript-eslint"

export default [
  {
    ignores: [".next/**", "node_modules/**", "next-env.d.ts"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "no-undef": "off",
      "react-hooks/exhaustive-deps": "warn",
      "react-hooks/rules-of-hooks": "error",
    },
  },
]
