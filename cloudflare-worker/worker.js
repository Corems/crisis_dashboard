export default {
  async fetch(request) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);
    const videoId = url.searchParams.get('videoId');

    if (!videoId) {
      return Response.json({ error: 'Missing videoId parameter' }, { status: 400, headers: corsHeaders });
    }

    try {
      const transcript = await fetchTranscript(videoId);
      return new Response(transcript, {
        headers: { ...corsHeaders, 'Content-Type': 'text/plain; charset=utf-8' },
      });
    } catch (err) {
      return Response.json({ error: err.message }, { status: 500, headers: corsHeaders });
    }
  },
};

async function fetchTranscript(videoId) {
  // Step 1: отримати caption tracks через InnerTube API
  const innerTubeResp = await fetch('https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'X-YouTube-Client-Name': '1',
      'X-YouTube-Client-Version': '2.20231121.08.00',
    },
    body: JSON.stringify({
      videoId,
      context: {
        client: {
          clientName: 'WEB',
          clientVersion: '2.20231121.08.00',
          hl: 'en',
          gl: 'US',
        },
      },
    }),
  });

  if (!innerTubeResp.ok) {
    throw new Error(`InnerTube API failed: ${innerTubeResp.status}`);
  }

  const data = await innerTubeResp.json();

  const captionTracks = data?.captions?.playerCaptionsTracklistRenderer?.captionTracks;

  if (!captionTracks || captionTracks.length === 0) {
    throw new Error('No captions available for this video');
  }

  // Priority: manual > english ASR > any
  const manualTracks = captionTracks.filter(t => t.kind !== 'asr');
  const asrEn = captionTracks.find(t => t.kind === 'asr' && t.languageCode === 'en');
  const selected = manualTracks[0] || asrEn || captionTracks[0];

  // Step 2: fetch caption XML
  let captionUrl = selected.baseUrl;
  if (!captionUrl.includes('fmt=')) {
    captionUrl += '&fmt=3';
  } else {
    captionUrl = captionUrl.replace(/fmt=\d+/, 'fmt=3');
  }

  const captionResp = await fetch(captionUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
  });

  if (!captionResp.ok) {
    throw new Error('Failed to fetch captions');
  }

  const text = await captionResp.text();

  if (text.trimStart().startsWith('<?xml') || text.trimStart().startsWith('<transcript')) {
    return parseXmlTranscript(text);
  }

  return text.trim();
}

function parseXmlTranscript(xml) {
  const lines = [];
  const regex = /<text[^>]*>(.*?)<\/text>/gs;
  let match;
  while ((match = regex.exec(xml)) !== null) {
    let line = match[1]
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/\n/g, ' ')
      .trim();
    if (line) lines.push(line);
  }
  return lines.join(' ');
}
