export const formatDescription = (text: string) => {
  if (!text) return text;
  return text.replace(
    /\*\*Example \d+:\*\*\n([\s\S]*?)(?=\n\n|$)/g,
    (match) => {
      const lines = match.split('\n');
      const title = lines[0]; // **Example X:**
      const preLines = lines.slice(1).map(line => {
        if (line.trim().startsWith('- **')) {
          return line.replace(/- \*\*(.*?)\*\*\s*(.*)/, (m, p1, p2) => {
            const cleanP2 = p2.replace(/^`|`$/g, '');
            return `<strong>${p1}</strong> ${cleanP2}`;
          });
        }
        return line;
      });
      return `${title}\n\n<pre>\n${preLines.join('\n')}\n</pre>\n\n`;
    }
  );
};
