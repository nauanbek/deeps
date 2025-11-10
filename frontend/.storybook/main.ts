const config = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  staticDirs: ['../public'],
  typescript: {
    check: false,
    reactDocgen: false,
  },
  core: {
    disableTelemetry: true,
  },
  webpackFinal: async (config) => {
    // Add support for TypeScript
    if (config.resolve) {
      config.resolve.extensions = ['.ts', '.tsx', '.js', '.jsx'];
    }

    // Add support for CSS modules and PostCSS (for Tailwind)
    if (config.module && config.module.rules) {
      config.module.rules.push({
        test: /\.css$/,
        use: [
          'style-loader',
          'css-loader',
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [require('tailwindcss'), require('autoprefixer')],
              },
            },
          },
        ],
      });
    }

    return config;
  },
};

export default config;
