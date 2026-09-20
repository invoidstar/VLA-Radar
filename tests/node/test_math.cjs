const assert=require('node:assert/strict');
const M=require('../../site/js/core/math.js');

let html=M.renderText('动作 $a_t = \\frac{\\Delta x}{\\Delta t}$');
assert(html.includes('<math'));
assert(html.includes('<msub>'));
assert(html.includes('<mfrac>'));
assert(html.includes('Δ'));
assert(!html.includes('$a_t'));

html=M.renderText('\\[L = \\sum_{t=1}^{T} \\lVert a_t-\\hat{a}_t \\rVert^2\\]');
assert(html.includes('math-display'));
assert(html.includes('<msubsup>'));
assert(html.includes('<mover'));
assert(html.includes('display="block"'));

html=M.renderParagraphs(`前文
\\[
L = \\sum_{t=1}^{T} \\lVert a_t-\\hat{a}_t \\rVert^2
\\]
后文`);
assert.equal((html.match(/<math/g)||[]).length,1);
assert(html.includes('math-display'));
assert(!html.includes('\\\\['));
assert(!html.includes('\\\\]'));
assert(html.includes('<p>前文</p>')&&html.includes('<p>后文</p>'));

html=M.renderText('矩阵 $A=\\begin{bmatrix}1 & 2 \\\\ 3 & 4\\end{bmatrix}$');
assert(html.includes('<mtable>'));
assert(html.includes('stretchy="true"'));

html=M.renderText('保持价格 \\$5，且 <script>alert(1)</script> 不执行');
assert(html.includes('$5'));
assert(html.includes('&lt;script&gt;'));
assert(!html.includes('<script>'));

html=M.renderText('未闭合公式 $x_t + 1');
assert(html.includes('$x_t + 1'));
assert(!html.includes('<math'));

const R=require('../../site/js/features/research/research.js');
html=R.noteBlocks('| Method | Loss |\n|---|---|\n| safe | $L=\\frac{1}{N}\\sum_i e_i$ |');
assert(html.includes('<table'));
assert(html.includes('<math'));
assert(html.includes('<mfrac>'));

console.log('PASS: local MathML rendering, delimiters, scripts, fractions, sums, matrices, escaping and table formulas');
