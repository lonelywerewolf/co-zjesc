import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Co zjeść? — planer posiłków",
    short_name: "Co zjeść?",
    description: "Tygodniowy plan śniadań i obiadów z produktów z Lidla, Biedronki i innych sklepów.",
    start_url: "/",
    display: "standalone",
    background_color: "#f7f5ef",
    theme_color: "#2f6b3a",
    lang: "pl",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
