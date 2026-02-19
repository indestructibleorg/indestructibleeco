export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/webhook/whatsapp")) return new Response("ok");
    if (url.pathname.startsWith("/webhook/telegram")) return new Response("ok");
    if (url.pathname.startsWith("/webhook/line")) return new Response("ok");
    if (url.pathname.startsWith("/webhook/messenger")) return new Response("ok");
    return new Response("Not found", { status: 404 });
  }
};
