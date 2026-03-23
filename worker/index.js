export default {
  async fetch(request, env) {

    // 处理 CORS 预检请求
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      });
    }

    const url = new URL(request.url);

    // 路由：POST /api/update — 写入每日评分数据
    if (request.method === 'POST' && url.pathname === '/api/update') {

      // 验证写入密钥
      const authHeader = request.headers.get('Authorization');
      const token = authHeader ? authHeader.replace('Bearer ', '') : '';
      if (token !== env.WRITE_TOKEN) {
        return new Response(
          JSON.stringify({ error: '未授权，Token 不正确' }),
          { status: 401, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // 解析请求体
      let data;
      try {
        data = await request.json();
      } catch (e) {
        return new Response(
          JSON.stringify({ error: '请求体格式错误，需要 JSON' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // 写入 D1 数据库，日期重复时更新
      try {
        await env.DB.prepare(`
          INSERT INTO daily_scores
            (date, condition1_score, condition2_score, condition3_score,
             overall_signal, tips_yield, hy_spread, fed_balance, dollar_index)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
          ON CONFLICT(date) DO UPDATE SET
            condition1_score = excluded.condition1_score,
            condition2_score = excluded.condition2_score,
            condition3_score = excluded.condition3_score,
            overall_signal = excluded.overall_signal,
            tips_yield = excluded.tips_yield,
            hy_spread = excluded.hy_spread,
            fed_balance = excluded.fed_balance,
            dollar_index = excluded.dollar_index
        `).bind(
          data.date,
          data.condition1_score,
          data.condition2_score,
          data.condition3_score,
          data.overall_signal,
          data.tips_yield,
          data.hy_spread,
          data.fed_balance,
          data.dollar_index
        ).run();

        return new Response(
          JSON.stringify({ success: true, date: data.date }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
            },
          }
        );
      } catch (e) {
        return new Response(
          JSON.stringify({ error: '数据库写入失败', detail: e.message }),
          { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // 路由：GET /api/scores — 读取最近 180 天评分数据
    if (request.method === 'GET' && url.pathname === '/api/scores') {
      try {
        const { results } = await env.DB.prepare(`
          SELECT date, condition1_score, condition2_score, condition3_score,
                 overall_signal, tips_yield, hy_spread, fed_balance, dollar_index
          FROM daily_scores
          ORDER BY date DESC
          LIMIT 180
        `).all();

        return new Response(
          JSON.stringify({ success: true, data: results }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
            },
          }
        );
      } catch (e) {
        return new Response(
          JSON.stringify({ error: '数据库查询失败', detail: e.message }),
          { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // 路由：GET /api/latest — 读取最新一条数据
    if (request.method === 'GET' && url.pathname === '/api/latest') {
      try {
        const result = await env.DB.prepare(`
          SELECT date, condition1_score, condition2_score, condition3_score,
                 overall_signal, tips_yield, hy_spread, fed_balance, dollar_index
          FROM daily_scores
          ORDER BY date DESC
          LIMIT 1
        `).first();

        return new Response(
          JSON.stringify({ success: true, data: result }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
            },
          }
        );
      } catch (e) {
        return new Response(
          JSON.stringify({ error: '数据库查询失败', detail: e.message }),
          { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // 默认响应
    return new Response(
      JSON.stringify({
        name: 'Gold Signal Worker',
        endpoints: [
          'POST /api/update — 写入每日评分（需要 Authorization header）',
          'GET /api/scores — 读取最近 180 天数据',
          'GET /api/latest — 读取最新一条数据',
        ]
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  },
};
