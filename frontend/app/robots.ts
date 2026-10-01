import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {

  return {

    rules: {

      userAgent: "*",

      allow: "/",

      disallow: [

        "/login",

        "/register",

        "/history",

        "/subscriptions",

        "/admin",

      ],

    },

    sitemap: "https://www.apexiveai.com/sitemap.xml",

  };

}