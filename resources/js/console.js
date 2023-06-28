/* Not used directly*/

var console_elems = {}
console_elems.stl = document.createElement('style');
console_elems.stl.textContent = `
:root {
    --font-title: 'Lato', 'Lucida Grande', 'Lucida Sans Unicode', Tahoma, Sans-Serif;
}
.console-title {
    font-family: var(--font-title);
    font-weight: 700;
    color: black;
    font-size: 1.1rem;
    line-height: 1;
    padding: 9px 10px;
    white-space: nowrap;
    margin: 0;
}
`;
document.head.appendChild(console_elems.stl);
console_elems.h_title = document.createElement('h2');
console_elems.h_title.className = 'console-title';
console_elems.h_title.textContent = 'Console:';
document.getElementById('output-footer').appendChild(console_elems.h_title);

function c_msg(type, o_func, ...args) {
    let p = document.createElement("p");
    p.classList.add(`console-${type}`);
    p.textContent = args.join(" ");
    document.getElementById('console-box').appendChild(p);
    o_func(...args);
}

const o_log = console.log.bind(console)
const o_error = console.error.bind(console);
const o_warn = console.warn.bind(console);

console.log = c_msg.bind(console, 'log', o_log);
console.error = c_msg.bind(console, 'error', o_error);
console.warn = c_msg.bind(console, 'warn', o_warn);

window.addEventListener("error", (event) => {
    console.error(`${event.type}: ${event.message}`);
});

var console_elems = {}
console_elems.stl = document.createElement('style');
console_elems.stl.textContent = `
:root {
    --font-log: Consolas, Monaco, 'Courier New', monospace;
}

.console-box {
    max-width: 70vw;
}

.console-error, .console-log, .console-warn {
    font-family: var(--font-log);
    white-space: nowrap;
    font-weight: 520;
    font-size: 0.9rem;
    line-height: 1.1rem;
    padding: 2px 10px;
    overflow-y: auto;
    border-bottom: 1px solid #A9A9A9;
    color: black;
    margin: 0;
}

.console-error {
    color: #8B0000;
    border-bottom-color: #FFC0CB;
    background-color: #FFE4E1;
}

.console-warn {
    color: #A0522D;
    border-bottom-color: #FFDEAD;
    background-color: #FFFACD;
}

@media (max-width: 600px) {
    .console-box {
        max-width: 95vw;
    }
}

@media (max-width: 992px) {
    .console-box {
        max-width: 90vw;
    }
}

@media (min-width: 993px) {
    .console-box {
        max-width: 85vw;
    }
}

@media (min-width: 1200px) {
    .console-box {
        max-width: 70vw;
    }
}
`;
document.head.appendChild(console_elems.stl);
console_elems.c_box = document.createElement('div');
console_elems.c_box.className = 'console-box';
console_elems.c_box.id = 'console-box';
document.getElementById('output-footer').appendChild(console_elems.c_box);
