export const siteNavigationGroups = [
  {
    label: "Explore",
    links: [
      { label: "Forums", href: "/forums" },
      { label: "Articles", href: "/articles" },
      { label: "Resources", href: "/resources" },
      { label: "Search", href: "/search" },
      { label: "Page 1–100", href: "/page/1" },
    ],
  },
  {
    label: "Solutions",
    links: [
      { label: "Trademark Intelligence", href: "/trademark-intelligence" },
      { label: "Workforce", href: "/workforce" },
      { label: "Phase 1", href: "/phase-1" },
    ],
  },
  {
    label: "Your account",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "History", href: "/history" },
      { label: "Pricing", href: "/pricing" },
      { label: "Subscriptions", href: "/subscriptions" },
      { label: "Checkout", href: "/checkout" },
      { label: "Login", href: "/login" },
      { label: "Register", href: "/register" },
      { label: "Admin", href: "/admin" },
    ],
  },
] as const;
