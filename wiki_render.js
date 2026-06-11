/**
 * 智联学习云 — Markdown 渲染器 (Wiki.js 风格)
 */

const Wiki = {
  parse(md) {
    // 统一换行符
    md = md.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    // 去掉 YAML front matter
    md = md.replace(/^---\n[\s\S]*?\n---\n?/, '');

    let lines = md.split('\n');
    let out = [];
    let i = 0;
    let pendingInlineClass = ''; // 给下一个块的内联 {.class}

    function flushPending() {
      if (pendingInlineClass) {
        // 找前一个块级标签，加 class
        for (let j = out.length - 1; j >= 0; j--) {
          let m = out[j].match(/^<(blockquote|ul|ol|p|h[1-6]|pre|table)([^>]*)>/);
          if (m) {
            let tag = m[0];
            if (!tag.includes('class=')) {
              out[j] = out[j].replace(tag, tag.replace('>', ' class="' + pendingInlineClass + '">'));
            }
            break;
          }
        }
        pendingInlineClass = '';
      }
    }

    while (i < lines.length) {
      let line = lines[i];

      // === 代码块 ===
      if (line.trim().startsWith('```')) {
        let lang = line.trim().slice(3);
        let codeLines = [];
        i++;
        while (i < lines.length && !lines[i].trim().startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        out.push('<pre class="code-block"><code>' + this.esc(codeLines.join('\n')) + '</code></pre>');
        i++; // skip closing ```
        continue;
      }

      // === 标题 ===
      let h = line.match(/^(#{1,6}) (.+)$/);
      if (h) {
        flushPending();
        let level = h[1].length;
        out.push('<h' + level + '>' + h[2] + '</h' + level + '>');
        i++; continue;
      }

      // === 水平线 ===
      if (line.trim() === '---') {
        flushPending();
        out.push('<hr>');
        i++; continue;
      }

      // === 表格 ===
      if (line.trim().startsWith('|') && i + 2 < lines.length && lines[i+1].trim().match(/^\|[-| :]+\|$/)) {
        flushPending();
        let headerCells = line.split('|').filter(c => c.trim()).map(c => '<th>' + c.trim() + '</th>').join('');
        let table = '<table class="wiki-table"><thead><tr>' + headerCells + '</tr></thead><tbody>';
        i += 2; // skip header and separator
        while (i < lines.length && lines[i].trim().startsWith('|')) {
          let cells = lines[i].split('|').filter(c => c.trim()).map(c => '<td>' + this._inline(c.trim()) + '</td>').join('');
          table += '<tr>' + cells + '</tr>';
          i++;
        }
        table += '</tbody></table>';
        out.push(table);
        continue;
      }

      // === 引用块 ===
      if (line.startsWith('> ')) {
        let bqLines = [];
        let bqClass = '';
        while (i < lines.length && lines[i].startsWith('> ')) {
          let content = lines[i].slice(2);
          // 内联 {.class}
          let cm = content.match(/\{\.(is-\w+)\}\s*$/);
          if (cm) { bqClass = cm[1]; content = content.replace(/\{\.(is-\w+)\}\s*$/, ''); }
          bqLines.push(content);
          i++;
        }
        // 检测下一行独立 {.class}
        if (i < lines.length) {
          let nc = lines[i].match(/^\{\.(is-\w+|grid-\w+)\}$/);
          if (nc) { bqClass = bqClass || nc[1]; i++; }
        }
        let inner = bqLines.map(l => '<p>' + this._inline(l) + '</p>').join('');
        if (bqClass) {
          out.push('<blockquote class="' + bqClass + '">' + inner + '</blockquote>');
        } else {
          out.push('<blockquote>' + inner + '</blockquote>');
        }
        continue;
      }

      // === Wiki.js 独立 {.class} ===
      let sc = line.match(/^\{\.(is-\w+|grid-\w+)\}$/);
      if (sc) {
        // 找前一个块元素加 class
        for (let j = out.length - 1; j >= 0; j--) {
          let m = out[j].match(/^<(blockquote|ul|ol|p|h[1-6]|pre|table)([^>]*)>/);
          if (m && !out[j].includes('class=')) {
            out[j] = out[j].replace(m[0], m[0].replace('>', ' class="' + sc[1] + '">'));
            break;
          }
        }
        i++; continue;
      }

      // === 无序列表 ===
      if (line.match(/^[*-] /)) {
        flushPending();
        let items = [];
        let listClass = '';
        while (i < lines.length && lines[i].match(/^[*-] /)) {
          let text = lines[i].replace(/^[*-] /, '');
          let cm = text.match(/\{\.(is-\w+)\}\s*$/);
          if (cm) { text = text.replace(/\{\.(is-\w+)\}\s*$/, ''); }
          items.push('<li>' + this._inline(text) + '</li>');
          i++;
        }
        if (i < lines.length) {
          let nc = lines[i].match(/^\{\.(grid-\w+)\}$/);
          if (nc) { listClass = nc[1]; i++; }
        }
        out.push('<ul' + (listClass ? ' class="' + listClass + '"' : '') + '>' + items.join('') + '</ul>');
        continue;
      }

      // === 有序列表 ===
      if (line.match(/^\d+\. /)) {
        flushPending();
        let items = [];
        while (i < lines.length && lines[i].match(/^\d+\. /)) {
          let text = lines[i].replace(/^\d+\. /, '');
          items.push('<li>' + this._inline(text) + '</li>');
          i++;
        }
        if (i < lines.length && lines[i].match(/^\{\.(grid-\w+)\}$/)) { i++; }
        out.push('<ol>' + items.join('') + '</ol>');
        continue;
      }

      // === 普通段落 ===
      if (line.trim()) {
        flushPending();
        out.push('<p>' + this._inline(line.trim()) + '</p>');
        i++; continue;
      }

      i++; // skip blank line
    }

    flushPending();
    return out.join('\n');
  },

  /** 行内格式 */
  _inline(text) {
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    text = text.replace(/!\[([^\]]*)\]\(([^)]+?)(\s*=\d+x)?\)/g, (m, alt, src, size) => {
      let s = size ? ' width="' + size.trim().replace('=','').split('x')[0] + '"' : '';
      return '<img src="' + src + '" alt="' + alt + '" class="wiki-img"' + s + '>';
    });
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)\{target="_blank"\}/g, '<a href="$2" target="_blank" class="wiki-link">$1</a>');
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="wiki-link">$1</a>');
    text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    text = text.replace(/~~(.+?)~~/g, '<del>$1</del>');
    return text;
  },

  esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); },

  FILE_LIST: [
    { name: 'C语言全能实战', file: 'courses_resource/c_language/home.md' },
    { name: 'Dev-C++ 使用指南', file: 'courses_resource/c_language/devcpp_usage.md' },
    { name: '算法与数据结构', file: 'courses_resource/datastruct/datastruct.md' },
    { name: '计算机基础', file: 'courses_resource/computer_base/computer_base.md' },
    { name: 'C++零基础到高级', file: 'courses_resource/cpp_language/home.md' },
    { name: '算法竞赛通关班', file: 'courses_resource/csp/home.md' },
    { name: 'C++高性能服务器', file: 'courses_resource/cpp_project_server/home.md' },
    { name: 'AI大模型入门', file: 'courses_resource/ai_mllm_aigc/home.md' },
    { name: '海贼学习指南', file: 'courses_resource/haizeix_guide/home.md' },
    { name: 'Linux系统编程实战', file: 'courses_resource/linux_program/home.md' },
    { name: 'Linux命令速查', file: 'courses_resource/linux_program/linux_commands.md' },
    { name: 'C++高薪就业', file: 'courses_resource/cpp_high_salary/home.md' },
  ]
};
