// Serverless proxy for Netlify — the browser can't call ai.hackclub.com
// directly (their CORS only allows their own origin), so we relay the request
// from the server side here. Mirrors what server.py does for local runs.

const HACKCLUB = 'https://ai.hackclub.com/proxy/v1/chat/completions';

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return json(405, { error: { message: 'POST only' } });
  }

  let upstream, body, status;
  try {
    upstream = await fetch(HACKCLUB, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': event.headers.authorization || event.headers.Authorization || '',
      },
      body: event.body,
    });
    body = await upstream.text();
    status = upstream.status;
  } catch (e) {
    return json(502, { error: { message: String(e) } });
  }

  // Hack Club sometimes replies with plain text or nothing (e.g. auth errors) —
  // always hand the browser valid JSON so it never chokes parsing.
  try {
    JSON.parse(body);
  } catch {
    body = JSON.stringify({ error: { message: body.trim() || 'HTTP ' + status } });
  }

  return {
    statusCode: status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    body,
  };
};

function json(statusCode, obj) {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(obj),
  };
}
