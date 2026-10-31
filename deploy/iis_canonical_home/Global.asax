<%@ Application Language="C#" %>
<script runat="server">
    internal static string CanonicalHomeTarget(string rawUrl, string method, bool secure, string authority)
    {
        if (!secure || !System.String.Equals(authority, "www.joinlinksmart.com", System.StringComparison.OrdinalIgnoreCase))
            return null;
        if (method != "GET" && method != "HEAD")
            return null;
        if (System.String.IsNullOrEmpty(rawUrl) || rawUrl.Length > 8192 ||
            rawUrl.IndexOf('\r') >= 0 || rawUrl.IndexOf('\n') >= 0 ||
            rawUrl.IndexOf('\0') >= 0 || rawUrl.IndexOf('\\') >= 0)
            return null;
        int queryIndex = rawUrl.IndexOf('?');
        string route = queryIndex < 0 ? rawUrl : rawUrl.Substring(0, queryIndex);
        if (!System.String.Equals(route, "/zhumadian", System.StringComparison.Ordinal))
            return null;
        return "/zhumadian/" + (queryIndex < 0 ? System.String.Empty : rawUrl.Substring(queryIndex));
    }

    void Application_BeginRequest(object sender, System.EventArgs e)
    {
        string target = CanonicalHomeTarget(Request.RawUrl, Request.HttpMethod,
            Request.IsSecureConnection, Request.Url.Authority);
        if (target == null)
            return;
        Response.RedirectPermanent(target, false);
        CompleteRequest();
    }
</script>
