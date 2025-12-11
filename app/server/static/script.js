// Interactive features and animations

document.addEventListener('DOMContentLoaded', function() {
    // Animated background dots
    createAnimatedBackground();
    
    // Dropdown functionality
    const researchDropdown = document.getElementById('researchDropdown');
    if (researchDropdown) {
        researchDropdown.addEventListener('click', function() {
            // Toggle dropdown (you can add actual dropdown menu here)
            this.classList.toggle('active');
        });
    }
    
    // Modal functionality
    const modalOverlay = document.getElementById('modalOverlay');
    const modalClose = document.getElementById('modalClose');
    
    // Open modal (can be triggered by various buttons)
    function openModal() {
        if (modalOverlay) {
            modalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    // Close modal
    function closeModal() {
        if (modalOverlay) {
            modalOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay) {
                closeModal();
            }
        });
    }
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modalOverlay && modalOverlay.classList.contains('active')) {
            closeModal();
        }
    });
    
    // Search input functionality
    const mainSearchInput = document.getElementById('mainSearchInput');
    const beginBtn = document.getElementById('beginBtn');
    
    if (mainSearchInput) {
        // Allow Enter key to trigger research
        mainSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleResearch();
            }
        });
        
        // Handle @ mentions
        mainSearchInput.addEventListener('input', function(e) {
            const value = e.target.value;
            if (value.includes('@')) {
                // You can add mention functionality here
                console.log('Mention detected');
            }
        });
    }
    
    // Begin Research button
    if (beginBtn) {
        beginBtn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
            
            handleResearch();
        });
    }
    
    // Handle research action -> call backend /api/run_query
    function handleResearch() {
        const question = mainSearchInput ? mainSearchInput.value.trim() : '';
        const statusBar = document.getElementById('statusBar');
        const summaryWrap = document.getElementById('summaryWrap');
        const summaryMd = document.getElementById('summaryMd');
        const rankingWrap = document.getElementById('rankingWrap');
        const rankingTable = document.getElementById('rankingTable');
        const reportLink = document.getElementById('reportLink');

        // Validation
        if (!question) {
            if (mainSearchInput) {
                mainSearchInput.style.animation = 'shake 0.5s';
                mainSearchInput.placeholder = 'Please enter a research question';
                setTimeout(() => { 
                    mainSearchInput.style.animation = ''; 
                    mainSearchInput.placeholder = 'Ask anything. Type @ for mentions.';
                }, 500);
            }
            return;
        }
        
        if (question.length < 10) {
            if (statusBar) {
                statusBar.hidden = false;
                statusBar.textContent = 'Question must be at least 10 characters';
                statusBar.style.background = '#ff4444';
                setTimeout(() => { statusBar.hidden = true; statusBar.style.background = ''; }, 3000);
            }
            return;
        }

        // Reset previous output
        if (summaryWrap) { summaryWrap.hidden = true; }
        if (rankingWrap) { rankingWrap.hidden = true; }
        if (reportLink) { reportLink.hidden = true; reportLink.innerHTML=''; }
        if (rankingTable) { const tb = rankingTable.querySelector('tbody'); if (tb) tb.innerHTML=''; }
        if (summaryMd) { summaryMd.innerHTML=''; }

        if (statusBar) {
            statusBar.hidden = false;
            statusBar.classList.add('loading');
            statusBar.style.background = '';
            statusBar.textContent = 'Orchestrating agents and gathering intelligence…';
        }
        if (beginBtn) { beginBtn.disabled = true; beginBtn.style.opacity='0.65'; }
        if (mainSearchInput) { mainSearchInput.disabled = true; }

        const startTime = Date.now();
        let progressInterval = null;
        
        // Show progress updates
        const progressMessages = [
            'Searching for candidate diseases…',
            'Gathering market intelligence…',
            'Analyzing clinical trials…',
            'Querying internal knowledge base…',
            'Synthesizing insights…'
        ];
        let msgIndex = 0;
        
        progressInterval = setInterval(() => {
            msgIndex = (msgIndex + 1) % progressMessages.length;
            if (statusBar && !statusBar.hidden) {
                statusBar.textContent = progressMessages[msgIndex];
            }
        }, 3000);

        fetch('/api/run_query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        })
        .then(r => {
            if (!r.ok) {
                throw new Error(`Server returned ${r.status}: ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            clearInterval(progressInterval);
            
            if (data && data.error){
                if (statusBar){
                    statusBar.textContent = 'Error: ' + data.error;
                    statusBar.classList.remove('loading');
                    statusBar.style.background = '#ff4444';
                }
                return;
            }
            
            // Display processing time
            const elapsed = data.processing_time_ms || (Date.now() - startTime);
            
            // Summary (markdown-rendered)
            if (summaryMd && data.summary) { 
                summaryMd.innerHTML = renderMarkdown(data.summary); 
            } else if (summaryMd) {
                summaryMd.innerHTML = '<p><em>No summary available</em></p>';
            }
            if (summaryWrap) { summaryWrap.hidden = false; }
            
            // Ranking
            if (Array.isArray(data.ranked) && data.ranked.length) {
                const tb = rankingTable.querySelector('tbody');
                data.ranked.forEach(r => {
                    const tr = document.createElement('tr');
                    const cells = [
                        r.disease,
                        (r.score ?? 0).toFixed(3),
                        (r.market_size_usd ?? 0).toLocaleString(),
                        r.competitor_count ?? 0,
                        r.phase2_india ?? 0,
                        r.phase3_india ?? 0,
                        r.trials_total_india ?? 0,
                    ];
                    cells.forEach(c => { 
                        const td = document.createElement('td'); 
                        td.textContent = c; 
                        tr.appendChild(td); 
                    });
                    tb.appendChild(tr);
                });
                rankingWrap.hidden = false;
            } else {
                console.warn('No ranking data received');
            }
            
            // Report link
            if (data.report_url && reportLink) {
                const a = document.createElement('a');
                a.href = data.report_url;
                a.textContent = '📄 Download PDF Report';
                a.download = 'medquery-report.pdf';
                reportLink.appendChild(a);
                reportLink.hidden = false;
            }
            
            if (statusBar) {
                statusBar.textContent = `Analysis complete ✓ (${(elapsed / 1000).toFixed(1)}s)`;
                statusBar.classList.remove('loading');
                statusBar.style.background = '#00BCD4';
                setTimeout(()=>{ statusBar.hidden = true; }, 3000);
            }
        })
        .catch(err => {
            clearInterval(progressInterval);
            console.error('Analysis failed:', err);
            if (statusBar) {
                statusBar.hidden = false;
                statusBar.classList.remove('loading');
                statusBar.style.background = '#ff4444';
                const errorMsg = err.message || 'Unknown error occurred';
                statusBar.textContent = `Error: ${errorMsg}. Please try again.`;
                setTimeout(() => { statusBar.hidden = true; statusBar.style.background = ''; }, 5000);
            }
        })
        .finally(()=>{
            clearInterval(progressInterval);
            if (beginBtn) { beginBtn.disabled = false; beginBtn.style.opacity='1'; }
            if (mainSearchInput) { mainSearchInput.disabled = false; mainSearchInput.focus(); }
        });
    }
    
    // Navigation tab switching
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            navTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Sidebar navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Search control buttons
    const searchControlBtns = document.querySelectorAll('.search-control-btn');
    searchControlBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Toggle active state (except primary button)
            if (!this.classList.contains('primary')) {
                const group = this.closest('.search-controls-left') || this.closest('.search-controls-right');
                if (group) {
                    group.querySelectorAll('.search-control-btn').forEach(b => {
                        if (!b.classList.contains('primary')) {
                            b.classList.remove('active');
                        }
                    });
                    this.classList.add('active');
                }
            }
        });
    });
    
    // Radio button interactions
    const radioOptions = document.querySelectorAll('.radio-option');
    radioOptions.forEach(option => {
        option.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });
    
    // Add scroll animations for cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe info cards
    document.querySelectorAll('.info-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // Parallax effect on mouse move
    let mouseX = 0;
    let mouseY = 0;
    
    document.addEventListener('mousemove', function(e) {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 10;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 10;
        
        const animatedBg = document.getElementById('animatedBg');
        if (animatedBg) {
            animatedBg.style.transform = `translate(${mouseX}px, ${mouseY}px)`;
        }
    });
});

// Create animated background with dots
function createAnimatedBackground() {
    const animatedBg = document.getElementById('animatedBg');
    if (!animatedBg) return;
    
    // Create multiple animated dots
    for (let i = 0; i < 20; i++) {
        const dot = document.createElement('div');
        dot.className = 'animated-dot';
        const size = Math.random() * 4 + 2;
        const duration = 3 + Math.random() * 4;
        const delay = Math.random() * 2;
        const left = Math.random() * 100;
        const top = Math.random() * 100;
        
        dot.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: rgba(0, 188, 212, 0.4);
            border-radius: 50%;
            left: ${left}%;
            top: ${top}%;
            animation: floatDot ${duration}s ease-in-out infinite;
            animation-delay: ${delay}s;
            pointer-events: none;
        `;
        
        animatedBg.appendChild(dot);
    }
}

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    @keyframes floatDot {
        0%, 100% {
            transform: translate(0, 0);
            opacity: 0.3;
        }
        50% {
            transform: translate(20px, -20px);
            opacity: 0.6;
        }
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .animated-dot {
        pointer-events: none;
    }
`;
document.head.appendChild(style);

// Lightweight markdown renderer (headings, lists, links, code, tables)
function renderMarkdown(md){
    if(!md) return '';
    // Normalize line endings
    md = md.replace(/\r\n?/g,'\n');
    // Escape HTML first
    const esc = s => s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
    // Extract code fences first to avoid interference
    const fences = [];
    md = md.replace(/```([\s\S]*?)```/g,(m,code)=>{const id=fences.push(code)-1;return `{{CODE_BLOCK_${id}}}`});

    // Headings
    md = md.replace(/^###\s+([^\n]+)$/gm,'<h3>$1<\/h3>')
           .replace(/^##\s+([^\n]+)$/gm,'<h2>$1<\/h2>')
           .replace(/^#\s+([^\n]+)$/gm,'<h1>$1<\/h1>');
    // Links, bold, italics
    md = md.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1<\/a>')
           .replace(/\*\*([^*]+)\*\*/g,'<strong>$1<\/strong>')
           .replace(/(^|\s)\*([^*]+)\*(?=\s|[.,!?:;]|$)/g,'$1<em>$2<\/em>');

    // Lists and paragraphs + simple table support
    const lines = md.split('\n');
    let html = '', inList=false, inTable=false, tableRows=[];
    const flushList = ()=>{ if(inList){ html+='</ul>'; inList=false; }};
    const flushTable = ()=>{
        if(!inTable) return;
        if(tableRows.length){
            const [head, ...rows] = tableRows;
            html += '<table><thead><tr>' + head.map(h=>`<th>${esc(h.trim())}</th>`).join('') + '</tr></thead><tbody>'+
                    rows.map(r=>'<tr>'+r.map(c=>`<td>${esc(c.trim())}</td>`).join('')+'</tr>').join('')+
                    '</tbody></table>';
        }
        tableRows = []; inTable=false;
    };
    for(let i=0;i<lines.length;i++){
        const line = lines[i];
        if(/^\s*\|.+\|\s*$/.test(line)){
            // Table-like row
            flushList();
            inTable = true;
            const cells = line.trim().slice(1,-1).split('|');
            // Skip separator rows (---)
            if(!/^\s*-{3,}\s*$/.test(cells[0])){
                tableRows.push(cells);
            }
            continue;
        } else if(/^\s*[-*]\s+/.test(line)){
            flushTable();
            if(!inList){ html+='<ul>'; inList=true; }
            html += '<li>'+line.replace(/^\s*[-*]\s+/, '')+'</li>';
            continue;
        } else if(line.trim()===''){
            flushList(); flushTable();
            html += '';
            continue;
        }
        flushList(); flushTable();
        if(!/^<h[1-3]>/.test(line)){
            html += '<p>'+line+'</p>';
        } else {
            html += line;
        }
    }
    flushList(); flushTable();

    // Restore fenced code blocks
    html = html.replace(/\{\{CODE_BLOCK_(\d+)\}\}/g,(m,idx)=>{
        const code = fences[Number(idx)] || '';
        return '<pre><code>'+esc(code)+'</code></pre>';
    });
    return html;
}
