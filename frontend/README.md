# Frontend Service

The frontend service is recommended to be a NextJS Web Application instead of a create-react-app as NextJS is stable and provides server components and other nice quality of life features.

## What is NextJS
NextJS is a framework for ReactJS development. It enables lots of quality of life features such as:
- React Server Components: rendered on the server
- Fast Startup
- Easy healthcheck endpoint
- Built-In Optimizations for Images, Fonts, etc...
- React Suspense functionality built in


## New Application

The repository is setup with a new application created by "create-next-app"

This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).


### Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

### Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Converting Create-React-App to NextJS

NextJS has a guide for converting existing create-react-apps to NextJS applications which can be found [here](https://nextjs.org/docs/app/building-your-application/upgrading/from-create-react-app#migration-steps)

The main steps are as follow, for more details please follow the above link:

1. Copy all files from your current create-react-app to the frontend "/src/app" directory

Make sure to merge the directories as the sample files will be needed for the next steps

2. Use NPM to install NextJS as a dependency:

```bash
yarn install next@latest
```

2. Create the next.config.mjs file

You can simply use the existing next.config.mjs file as it is configured with defaults

3. Update the tsconfig.json file

If your project has a tsconfig file, please ensure it contains all the values in the tsconfig.sample.json file. Otherwise you can simply use the tsconfg.sample.json file as your base (removing the ".sample" from the name)

4. Create the root layout file

Within "src/app" create a "layout.tsx" file which will act as the main layout for the application. You can utilize the [src/sample/layout.tsx](src/sample/layout.tsx) as base.

Ensure to place your favicon, icon.png and robots.txt at the root of the [src/app](src/app) directory

5. Styling

Any global styles should be imported into the root layout file
```javascript
import '../index.css'
```

6. Create Entrypoint Page

Next.JS uses folder hiarchies to create a page-based routing system. In order for your converted app to work we need to create a catch-all entrypoint. By default NextJS tries to compile as much of the application into static assets. Since we are using a ReactApp which needs to be dynamic, we create a "client" component which loads the ReactApp and informs NextJS that it should not be a static asset.

Copy the [[[...slug]]](src/sample/[[...slug]]) directory into your [src/app](src/app) to enable NextJS to properly run your CreateReactApp As is


7. Copy the "amplify" directory from the "sample" to the "app" directory.

8. Change environment variables. NextJS uses "NEXT_PUBLIC_" as a prefix for environment variables instead of "REACT_APP_" so simply changing the names wherever they are used will work (including in the .env files)

9. Update package.json scripts and gitignore files

The package.json scripts should look like this:
```json
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
```

Your gitignore file should include the additional following entries:
```gitignore
.next
next-env.d.ts
dist
```

10. Cleanup the CRA dependencies

you can now remove the following:
- src/index.tsx
- public/index.html
- reportWebVitals setup

uninstall the CRA dependency:
```bash
yarn remove react-scripts
```


11. Done

Now that your CRA app runs on NextJS you can incorporate the quality of life features of NextJS into your own application.