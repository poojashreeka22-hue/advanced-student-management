/**
 * EduTrack Enterprise - Application Client Controller
 * Full REST API integration with real data bindings, charts, multi-step forms, and modals.
 */

const API_BASE = '/api/v1';

class EduTrackApp {
  constructor() {
    this.currentTab = 'dashboard';
    this.students = [];
    this.filteredStudents = [];
    this.departments = [];
    this.courses = [];
    this.faculty = [];
    this.exams = [];
    this.invoices = [];
    this.currentPage = 1;
    this.pageSize = 10;
    this.deptChartInstance = null;
    this.gradeChartInstance = null;
    this.searchDebounceTimer = null;
    this.csvSelectedFile = null;
    this.csvPreviewData = null;

    this.init();
  }

  async init() {
    this.bindEvents();
    this.setupKeyboardShortcuts();
    this.setupCSVDragAndDrop();
    await this.refreshAllData();
  }

  bindEvents() {
    // Tab Navigation
    document.querySelectorAll('.nav-item[data-tab]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = btn.getAttribute('data-tab');
        this.switchTab(tab);
      });
    });

    // Mobile Sidebar Toggle
    const mobileToggle = document.getElementById('mobileToggleBtn');
    const mobileClose = document.getElementById('mobileCloseBtn');
    const sidebar = document.getElementById('sidebar');
    if (mobileToggle && sidebar) {
      mobileToggle.addEventListener('click', () => sidebar.classList.add('open'));
    }
    if (mobileClose && sidebar) {
      mobileClose.addEventListener('click', () => sidebar.classList.remove('open'));
    }

    // Top action buttons
    const topAddBtn = document.getElementById('topAddStudentBtn');
    if (topAddBtn) {
      topAddBtn.addEventListener('click', () => this.openAddStudentModal());
    }

    const quickSeedBtn = document.getElementById('quickSeedBtn');
    if (quickSeedBtn) {
      quickSeedBtn.addEventListener('click', () => this.seedDemoData());
    }

    // Global Search
    const globalSearch = document.getElementById('globalSearchInput');
    const clearBtn = document.getElementById('searchClearBtn');
    if (globalSearch) {
      globalSearch.addEventListener('input', (e) => {
        const val = e.target.value;
        if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';
        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => {
          this.switchTab('students');
          const dirSearch = document.getElementById('dirSearchInput');
          if (dirSearch) {
            dirSearch.value = val;
            this.filterStudentDirectory();
          }
        }, 250);
      });
    }
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (globalSearch) globalSearch.value = '';
        clearBtn.style.display = 'none';
        this.filterStudentDirectory();
      });
    }

    // Directory Filters
    const dirSearch = document.getElementById('dirSearchInput');
    const dirDept = document.getElementById('dirDeptFilter');
    const dirYear = document.getElementById('dirYearFilter');
    const dirStatus = document.getElementById('dirStatusFilter');
    const dirReset = document.getElementById('dirResetBtn');

    [dirSearch, dirDept, dirYear, dirStatus].forEach(el => {
      if (el) {
        el.addEventListener('input', () => this.filterStudentDirectory());
        el.addEventListener('change', () => this.filterStudentDirectory());
      }
    });

    if (dirReset) {
      dirReset.addEventListener('click', () => {
        if (dirSearch) dirSearch.value = '';
        if (dirDept) dirDept.value = '';
        if (dirYear) dirYear.value = '';
        if (dirStatus) dirStatus.value = '';
        this.filterStudentDirectory();
      });
    }

    // Pagination
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.addEventListener('click', () => this.changePage(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => this.changePage(1));

    // Multi-step Admission Form
    const admForm = document.getElementById('admissionForm');
    if (admForm) {
      admForm.addEventListener('submit', (e) => this.handleAdmissionSubmit(e));
    }

    // Attendance Roster Load
    const loadAttBtn = document.getElementById('loadAttendanceRosterBtn');
    if (loadAttBtn) {
      loadAttBtn.addEventListener('click', () => this.loadAttendanceRoster());
    }

    // Modal Forms
    const payForm = document.getElementById('paymentForm');
    if (payForm) payForm.addEventListener('submit', (e) => this.handlePaymentSubmit(e));

    const grdForm = document.getElementById('gradeForm');
    if (grdForm) grdForm.addEventListener('submit', (e) => this.handleGradeSubmit(e));

    const invForm = document.getElementById('invoiceForm');
    if (invForm) invForm.addEventListener('submit', (e) => this.handleInvoiceSubmit(e));

    const slotForm = document.getElementById('slotForm');
    if (slotForm) slotForm.addEventListener('submit', (e) => this.handleSlotSubmit(e));

    // Real-time 10-digit phone restrictions and counters
    this.setupPhoneInput('admPhone', 'admPhoneCounter', 'errPhone');
    this.setupPhoneInput('qckPhone', 'qckPhoneCounter', 'errQckPhone');
    this.setupPhoneInput('editPhone', 'editPhoneCounter', 'errEditPhone');
    this.setupPhoneInput('facPhone', 'facPhoneCounter', 'errFacPhone');

    // Real-time email validation
    this.setupEmailInput('admEmail', 'errEmail');
    this.setupEmailInput('qckEmail', 'errQckEmail');
    this.setupEmailInput('editEmail', 'errEditEmail');
    this.setupEmailInput('facEmail', 'errFacEmail');

    // Additional CRUD Forms
    const qckForm = document.getElementById('quickAddStudentForm');
    if (qckForm) qckForm.addEventListener('submit', (e) => this.handleQuickAddStudentSubmit(e));

    const editForm = document.getElementById('editStudentForm');
    if (editForm) editForm.addEventListener('submit', (e) => this.handleEditStudentSubmit(e));

    const deptForm = document.getElementById('deptForm');
    if (deptForm) deptForm.addEventListener('submit', (e) => this.handleDeptSubmit(e));

    const facForm = document.getElementById('facultyForm');
    if (facForm) facForm.addEventListener('submit', (e) => this.handleFacultySubmit(e));

    const crsForm = document.getElementById('courseForm');
    if (crsForm) crsForm.addEventListener('submit', (e) => this.handleCourseSubmit(e));

    const exmForm = document.getElementById('examScheduleForm');
    if (exmForm) exmForm.addEventListener('submit', (e) => this.handleExamSubmit(e));

    const clsForm = document.getElementById('classroomForm');
    if (clsForm) clsForm.addEventListener('submit', (e) => this.handleClassroomSubmit(e));
  }

  setupKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        const searchInput = document.getElementById('globalSearchInput');
        if (searchInput) searchInput.focus();
      }
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop.open').forEach(m => m.classList.remove('open'));
      }
    });
  }

  switchTab(tabName) {
    this.currentTab = tabName;
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-view').forEach(el => el.classList.remove('active'));

    const targetNav = document.querySelector(`.nav-item[data-tab="${tabName}"]`);
    if (targetNav) targetNav.classList.add('active');

    const targetView = document.getElementById(`view-${tabName}`);
    if (targetView) targetView.classList.add('active');

    // Close mobile drawer if open
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('open');

    // Refresh context data based on tab
    if (tabName === 'dashboard') this.refreshDashboard();
    if (tabName === 'students') this.filterStudentDirectory();
    if (tabName === 'departments') this.loadDepartmentsAndFaculty();
    if (tabName === 'courses') this.loadCourses();
    if (tabName === 'attendance') this.prepareAttendanceView();
    if (tabName === 'grades') this.loadExams();
    if (tabName === 'fees') this.loadFeeInvoices();
    if (tabName === 'timetable') this.loadTimetable();
    if (tabName === 'reports') this.loadReports();
    if (tabName === 'audit') this.loadAuditLogs();
  }

  async refreshAllData() {
    try {
      await Promise.all([
        this.loadStudents(),
        this.loadDepartmentsAndFaculty(),
        this.loadCourses()
      ]);
      await this.refreshDashboard();
    } catch (err) {
      console.error('Error initializing data:', err);
    }
  }

  // ==================== DASHBOARD & METRICS ====================
  async refreshDashboard() {
    try {
      const res = await fetch(`${API_BASE}/analytics/metrics`);
      if (!res.ok) throw new Error('Failed to load metrics');
      const data = await res.json();

      document.getElementById('kpiTotalStudents').textContent = data.total_students;
      document.getElementById('kpiActiveStudents').textContent = `${data.active_students} Active Students`;
      document.getElementById('kpiTotalCourses').textContent = data.total_courses;
      document.getElementById('kpiTotalFaculty').textContent = `${data.total_faculty} Faculty Assigned`;
      document.getElementById('kpiAttendanceRate').textContent = `${data.overall_attendance_rate.toFixed(1)}%`;
      document.getElementById('kpiFeesCollected').textContent = `₹${data.total_fees_collected.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById('kpiFeesOutstanding').textContent = `Outstanding: ₹${data.total_fees_outstanding.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

      this.renderDepartmentChart(data.department_distribution);
      await this.renderGradeDistributionChart();
      this.renderRecentStudentsTable();
    } catch (err) {
      console.warn('Metrics endpoint fallback:', err);
      // Fallback to legacy stats
      this.refreshLegacyStats();
    }
  }

  async refreshLegacyStats() {
    try {
      const res = await fetch('/stats');
      if (res.ok) {
        const data = await res.json();
        document.getElementById('kpiTotalStudents').textContent = data.total_students;
        this.renderDepartmentChart(data.department_counts);
      }
    } catch (e) {
      console.error(e);
    }
  }

  renderDepartmentChart(distribution) {
    const ctx = document.getElementById('deptChart');
    if (!ctx) return;

    const labels = Object.keys(distribution || {});
    const values = Object.values(distribution || {});

    if (this.deptChartInstance) {
      this.deptChartInstance.destroy();
    }

    if (typeof Chart === 'undefined') return;

    this.deptChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels.length ? labels : ['No Data'],
        datasets: [{
          data: values.length ? values : [1],
          backgroundColor: [
            '#2563eb', '#38bdf8', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899'
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
        }
      }
    });
  }

  async renderGradeDistributionChart() {
    const ctx = document.getElementById('gradeChart');
    if (!ctx || typeof Chart === 'undefined') return;

    try {
      const res = await fetch(`${API_BASE}/analytics/grades`);
      const data = res.ok ? await res.json() : [];

      const labels = data.map(d => d.letter_grade);
      const counts = data.map(d => d.count);

      if (this.gradeChartInstance) {
        this.gradeChartInstance.destroy();
      }

      this.gradeChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels.length ? labels : ['A+', 'A', 'B', 'C', 'D', 'F'],
          datasets: [{
            label: 'Students Count',
            data: counts.length ? counts : [0, 0, 0, 0, 0, 0],
            backgroundColor: '#2563eb',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, ticks: { precision: 0 } }
          },
          plugins: { legend: { display: false } }
        }
      });
    } catch (e) {
      console.warn(e);
    }
  }

  renderRecentStudentsTable() {
    const tbody = document.getElementById('dashboardRecentBody');
    if (!tbody) return;

    const recent = this.students.slice(-5).reverse();
    if (recent.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No students registered yet. Click "+ New Student" to admit.</td></tr>`;
      return;
    }

    tbody.innerHTML = recent.map(s => `
      <tr>
        <td><strong>${s.register_number}</strong></td>
        <td>${s.full_name}</td>
        <td>${s.department}</td>
        <td>${s.academic_year}</td>
        <td><span class="badge badge-${s.status || 'active'}">${s.status || 'active'}</span></td>
        <td>
          <button class="btn btn-sm btn-outline" onclick="app.viewStudentDossier(${s.id})">Inspect Dossier</button>
        </td>
      </tr>
    `).join('');
  }

  // ==================== STUDENTS DIRECTORY ====================
  async loadStudents() {
    try {
      const res = await fetch('/students');
      if (!res.ok) throw new Error('Failed to load students');
      this.students = await res.json();
      this.filteredStudents = [...this.students];
      const badge = document.getElementById('navStudentBadge');
      if (badge) badge.textContent = this.students.length;
      this.renderStudentsTable();
    } catch (err) {
      console.error(err);
      this.showToast('Could not load student list', 'error');
    }
  }

  filterStudentDirectory() {
    const q = (document.getElementById('dirSearchInput')?.value || '').trim().toLowerCase();
    const dept = (document.getElementById('dirDeptFilter')?.value || '').trim().toLowerCase();
    const year = (document.getElementById('dirYearFilter')?.value || '').trim().toLowerCase();
    const status = (document.getElementById('dirStatusFilter')?.value || '').trim().toLowerCase();

    this.filteredStudents = this.students.filter(s => {
      const matchQ = !q || (
        (s.full_name && s.full_name.toLowerCase().includes(q)) ||
        (s.register_number && s.register_number.toLowerCase().includes(q)) ||
        (s.email && s.email.toLowerCase().includes(q))
      );
      const matchDept = !dept || (s.department && s.department.toLowerCase() === dept);
      const matchYear = !year || (s.academic_year && s.academic_year.toLowerCase() === year);
      const matchStatus = !status || ((s.status || 'active').toLowerCase() === status);
      return matchQ && matchDept && matchYear && matchStatus;
    });

    this.currentPage = 1;
    this.renderStudentsTable();
  }

  renderStudentsTable() {
    const tbody = document.getElementById('studentsTableBody');
    if (!tbody) return;

    const total = this.filteredStudents.length;
    const start = (this.currentPage - 1) * this.pageSize;
    const end = Math.min(start + this.pageSize, total);
    const paged = this.filteredStudents.slice(start, end);

    const info = document.getElementById('paginationInfo');
    if (info) info.textContent = `Showing ${total === 0 ? 0 : start + 1} - ${end} of ${total} students`;

    const indicator = document.getElementById('pageIndicator');
    const totalPages = Math.ceil(total / this.pageSize) || 1;
    if (indicator) indicator.textContent = `Page ${this.currentPage} of ${totalPages}`;

    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;

    if (paged.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No student records matching your query.</td></tr>`;
      return;
    }

    tbody.innerHTML = paged.map(s => `
      <tr>
        <td><strong>${s.register_number}</strong></td>
        <td>${s.full_name}</td>
        <td>${s.email}</td>
        <td>${s.phone_number}</td>
        <td>${s.department}</td>
        <td>${s.academic_year} / Sem ${s.semester || 1}</td>
        <td><span class="badge badge-${s.status || 'active'}">${s.status || 'active'}</span></td>
        <td><strong>${(s.gpa || 0).toFixed(2)}</strong></td>
        <td>
          <div class="action-row">
            <button class="btn btn-sm btn-outline" onclick="app.viewStudentDossier(${s.id})" title="View Complete Dossier">Dossier</button>
            <button class="btn btn-sm btn-secondary" onclick="app.openEditStudentModal(${s.id})" title="Edit Student">✏️ Edit</button>
            <button class="btn btn-sm btn-danger" onclick="app.confirmDeleteStudent(${s.id}, '${s.full_name.replace(/'/g, "\\'")}')" title="Delete">✕</button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  changePage(delta) {
    this.currentPage += delta;
    this.renderStudentsTable();
  }

  // ==================== ADMISSION WIZARD ====================
  goToStep(stepNum) {
    document.querySelectorAll('.step-indicator .step').forEach((el, idx) => {
      if (idx + 1 === stepNum) el.classList.add('active');
      else if (idx + 1 < stepNum) el.classList.add('active');
      else el.classList.remove('active');
    });

    document.querySelectorAll('.form-step').forEach((el, idx) => {
      if (idx + 1 === stepNum) el.classList.add('active');
      else el.classList.remove('active');
    });
  }

  validateStep1AndNext() {
    const fullName = document.getElementById('admFullName').value.trim();
    const regNum = document.getElementById('admRegNumber').value.trim();
    let hasErr = false;

    if (!fullName || fullName.length < 2) {
      document.getElementById('errFullName').textContent = 'Full legal name must be at least 2 characters.';
      hasErr = true;
    } else {
      document.getElementById('errFullName').textContent = '';
    }

    if (!regNum || regNum.length < 2) {
      document.getElementById('errRegNumber').textContent = 'Register number must be at least 2 characters.';
      hasErr = true;
    } else {
      document.getElementById('errRegNumber').textContent = '';
    }

    if (!hasErr) this.goToStep(2);
  }

  validateStep2AndNext() {
    this.goToStep(3);
  }

  async handleAdmissionSubmit(e) {
    e.preventDefault();
    const fullName = document.getElementById('admFullName').value.trim();
    const regNum = document.getElementById('admRegNumber').value.trim();
    const email = document.getElementById('admEmail').value.trim();
    const phone = document.getElementById('admPhone').value.trim();

    let hasErr = false;

    if (!fullName || fullName.length < 2) {
      document.getElementById('errFullName').textContent = 'Full legal name must be at least 2 characters.';
      this.goToStep(1);
      return;
    }

    if (!regNum || regNum.length < 2) {
      document.getElementById('errRegNumber').textContent = 'Register number is required.';
      this.goToStep(1);
      return;
    }

    if (!this.isValidEmail(email)) {
      document.getElementById('errEmail').textContent = 'Please enter a valid email format (e.g. student@college.edu)';
      hasErr = true;
    } else {
      document.getElementById('errEmail').textContent = '';
    }

    const cleanPhone = phone.replace(/\D/g, '');
    if (cleanPhone.length !== 10) {
      document.getElementById('errPhone').textContent = 'Phone number must be exactly 10 digits (e.g. 9876543210)';
      hasErr = true;
    } else {
      document.getElementById('errPhone').textContent = '';
    }

    if (hasErr) return;

    const payload = {
      full_name: fullName,
      register_number: regNum,
      first_name: document.getElementById('admFirstName').value.trim() || undefined,
      last_name: document.getElementById('admLastName').value.trim() || undefined,
      date_of_birth: document.getElementById('admDob').value || undefined,
      gender: document.getElementById('admGender').value,
      department: document.getElementById('admDepartment').value,
      academic_year: document.getElementById('admAcademicYear').value,
      semester: parseInt(document.getElementById('admSemester').value, 10) || 1,
      status: document.getElementById('admStatus').value,
      admission_date: document.getElementById('admAdmissionDate').value || undefined,
      gpa: parseFloat(document.getElementById('admGpa').value) || 0.0,
      email: email,
      phone_number: cleanPhone,
      guardian_name: document.getElementById('admGuardianName').value.trim() || undefined,
      guardian_phone: document.getElementById('admGuardianPhone').value.trim() || undefined,
      address: document.getElementById('admAddress').value.trim() || undefined,
    };

    const submitBtn = document.getElementById('submitAdmissionBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing Admission...';

    try {
      const res = await fetch('/students', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(this.formatApiError(data, 'Failed to admit student'));
      }

      this.showToast(`Student ${data.full_name} (${data.register_number}) admitted successfully!`, 'success');
      document.getElementById('admissionForm').reset();
      const phoneCounter = document.getElementById('admPhoneCounter');
      if (phoneCounter) {
        phoneCounter.textContent = '0/10 digits';
        phoneCounter.classList.remove('valid');
      }
      this.goToStep(1);
      await this.loadStudents();
      this.refreshDashboard();
      this.switchTab('students');
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '✓ Complete Admission & Register';
    }
  }

  // ==================== STUDENT DOSSIER ====================
  async viewStudentDossier(studentId) {
    try {
      const res = await fetch(`${API_BASE}/students/${studentId}/dossier`);
      if (!res.ok) throw new Error('Failed to load dossier');
      const data = await res.json();

      document.getElementById('dossierStudentName').textContent = data.full_name;
      document.getElementById('dossierStudentReg').textContent = data.register_number;
      document.getElementById('dossierDept').textContent = data.department;
      document.getElementById('dossierGpa').textContent = (data.gpa || 0).toFixed(2);
      document.getElementById('dossierAttendance').textContent = `${(data.attendance_rate || 0).toFixed(1)}%`;
      document.getElementById('dossierFeeBalance').textContent = `₹${(data.outstanding_fee_balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

      const badge = document.getElementById('dossierStatusBadge');
      badge.textContent = data.status || 'active';
      badge.className = `badge badge-${data.status || 'active'}`;

      document.getElementById('dosEmail').textContent = data.email || 'N/A';
      document.getElementById('dosPhone').textContent = data.phone_number || 'N/A';
      document.getElementById('dosYear').textContent = data.academic_year || 'N/A';
      document.getElementById('dosSemester').textContent = `Semester ${data.semester || 1}`;
      document.getElementById('dosDob').textContent = data.date_of_birth || 'N/A';
      document.getElementById('dosGender').textContent = data.gender || 'N/A';
      document.getElementById('dosGuardian').textContent = `${data.guardian_name || 'N/A'} (${data.guardian_phone || 'N/A'})`;
      document.getElementById('dosAddress').textContent = data.address || 'N/A';

      // Load Transcript & Fees in background
      this.loadDossierTranscript(studentId);
      this.loadDossierFees(studentId);

      this.switchDossierTab('profile');
      this.openModal('dossierModal');
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  switchDossierTab(tab) {
    document.querySelectorAll('.dossier-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.dossier-tabs .tab-content').forEach(c => c.classList.remove('active'));

    if (tab === 'profile') {
      document.querySelector('.dossier-tabs .tab-btn:nth-child(1)').classList.add('active');
      document.getElementById('dossierTabProfile').classList.add('active');
    } else if (tab === 'transcript') {
      document.querySelector('.dossier-tabs .tab-btn:nth-child(2)').classList.add('active');
      document.getElementById('dossierTabTranscript').classList.add('active');
    } else if (tab === 'fees') {
      document.querySelector('.dossier-tabs .tab-btn:nth-child(3)').classList.add('active');
      document.getElementById('dossierTabFees').classList.add('active');
    }
  }

  async loadDossierTranscript(studentId) {
    const tbody = document.getElementById('dossierTranscriptBody');
    try {
      const res = await fetch(`${API_BASE}/students/${studentId}/transcript`);
      if (!res.ok) throw new Error();
      const data = await res.json();

      if (!data.items || data.items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-2 text-muted">No examination grades recorded yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.items.map(item => `
        <tr>
          <td><strong>${item.course_code}</strong></td>
          <td>${item.course_title}</td>
          <td>${item.credits}</td>
          <td>${item.marks_percentage.toFixed(1)}%</td>
          <td><span class="badge">${item.letter_grade}</span></td>
          <td><strong>${item.grade_point.toFixed(2)}</strong></td>
        </tr>
      `).join('');
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-2 text-muted">Transcript records not available.</td></tr>`;
    }
  }

  async loadDossierFees(studentId) {
    const tbody = document.getElementById('dossierFeesBody');
    try {
      const res = await fetch(`${API_BASE}/fees/invoices/student/${studentId}`);
      if (!res.ok) throw new Error();
      const invoices = await res.json();

      if (!invoices || invoices.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-2 text-muted">No fee invoices recorded.</td></tr>`;
        return;
      }

      tbody.innerHTML = invoices.map(inv => `
        <tr>
          <td><strong>${inv.invoice_number}</strong></td>
          <td>${inv.title}</td>
          <td>₹${inv.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
          <td>₹${inv.waiver_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
          <td>₹${inv.total_paid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
          <td class="text-danger"><strong>₹${inv.balance_due.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></td>
          <td><span class="badge badge-${inv.status}">${inv.status}</span></td>
        </tr>
      `).join('');
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-2 text-muted">Fee records not available.</td></tr>`;
    }
  }

  // ==================== DELETIONS ====================
  confirmDeleteStudent(studentId, studentName) {
    document.getElementById('confirmModalTitle').textContent = 'Confirm Student Deletion';
    document.getElementById('confirmModalMessage').textContent = `Are you sure you want to permanently delete student ${studentName}? This action removes enrollments, grades, and fee records.`;
    const actionBtn = document.getElementById('confirmModalActionBtn');
    actionBtn.onclick = () => this.executeDeleteStudent(studentId);
    this.openModal('confirmModal');
  }

  async executeDeleteStudent(studentId) {
    this.closeModal('confirmModal');
    try {
      const res = await fetch(`/students/${studentId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete student');
      this.showToast('Student deleted successfully', 'success');
      await this.loadStudents();
      this.refreshDashboard();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== ATTENDANCE ====================
  async prepareAttendanceView() {
    const select = document.getElementById('attCourseSelect');
    if (!select) return;
    select.innerHTML = '<option value="">-- Choose Course --</option>' +
      this.courses.map(c => `<option value="${c.id}">${c.code} — ${c.title}</option>`).join('');

    const dateInput = document.getElementById('attSessionDate');
    if (dateInput && !dateInput.value) {
      dateInput.value = new Date().toISOString().split('T')[0];
    }
  }

  loadAttendanceRoster() {
    const courseId = document.getElementById('attCourseSelect').value;
    if (!courseId) {
      this.showToast('Please select a course first', 'warning');
      return;
    }

    const card = document.getElementById('attendanceRosterCard');
    const tbody = document.getElementById('attendanceRosterBody');
    if (card) card.style.display = 'block';

    const roster = this.students.slice(0, 15);
    if (roster.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No students available.</td></tr>`;
      return;
    }

    tbody.innerHTML = roster.map(s => `
      <tr data-student-id="${s.id}">
        <td><strong>${s.register_number}</strong></td>
        <td>${s.full_name}</td>
        <td>${s.department}</td>
        <td>
          <div class="action-row">
            <label><input type="radio" name="att_status_${s.id}" value="present" checked /> Present</label>
            <label><input type="radio" name="att_status_${s.id}" value="late" /> Late</label>
            <label><input type="radio" name="att_status_${s.id}" value="absent" /> Absent</label>
            <label><input type="radio" name="att_status_${s.id}" value="excused" /> Excused</label>
          </div>
        </td>
        <td><input type="text" class="form-control att-note" placeholder="Optional notes" /></td>
      </tr>
    `).join('');
  }

  markAllAttendance(statusVal) {
    document.querySelectorAll('#attendanceRosterBody input[type="radio"]').forEach(r => {
      if (r.value === statusVal) r.checked = true;
    });
  }

  async submitBulkAttendance() {
    const courseId = parseInt(document.getElementById('attCourseSelect').value, 10);
    const date = document.getElementById('attSessionDate').value;
    const slot = parseInt(document.getElementById('attSlotSelect').value, 10);

    const rows = document.querySelectorAll('#attendanceRosterBody tr[data-student-id]');
    const records = [];
    rows.forEach(r => {
      const studentId = parseInt(r.getAttribute('data-student-id'), 10);
      const checked = r.querySelector(`input[name="att_status_${studentId}"]:checked`);
      const noteInput = r.querySelector('.att-note');
      records.push({
        student_id: studentId,
        status: checked ? checked.value : 'present',
        notes: noteInput ? noteInput.value : undefined
      });
    });

    try {
      const res = await fetch(`${API_BASE}/attendance/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: courseId,
          session_date: date,
          slot_number: slot,
          records: records
        })
      });
      if (!res.ok) throw new Error('Failed to record attendance');
      this.showToast(`Saved attendance for ${records.length} students!`, 'success');
      this.refreshDashboard();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== DEPARTMENTS & FACULTY ====================
  async loadDepartmentsAndFaculty() {
    try {
      const [deptRes, facRes] = await Promise.all([
        fetch(`${API_BASE}/departments`),
        fetch(`${API_BASE}/faculty`)
      ]);
      this.departments = deptRes.ok ? await deptRes.json() : [];
      this.faculty = facRes.ok ? await facRes.json() : [];

      const deptBody = document.getElementById('deptTableBody');
      const deptBadge = document.getElementById('deptCountBadge');
      if (deptBadge) deptBadge.textContent = `${this.departments.length} Total`;
      if (deptBody) {
        deptBody.innerHTML = this.departments.map(d => `
          <tr>
            <td><strong>${d.code}</strong></td>
            <td>${d.name}</td>
            <td>
              <span class="badge ${d.hod_faculty_id ? 'badge-active' : 'badge-suspended'}">
                ${d.head_of_department || 'Vacant / Not Assigned'}
              </span>
            </td>
            <td>${d.building || 'N/A'}</td>
            <td>₹${(d.budget || 0).toLocaleString('en-IN')}</td>
            <td>
              <button class="btn btn-sm btn-outline" onclick="app.openAssignHodModal(${d.id})">
                ${d.hod_faculty_id ? '⚙ Change HOD' : '+ Assign HOD'}
              </button>
            </td>
          </tr>
        `).join('');
      }

      const facBody = document.getElementById('facultyTableBody');
      const facBadge = document.getElementById('facultyCountBadge');
      if (facBadge) facBadge.textContent = `${this.faculty.length} Total`;
      if (facBody) {
        facBody.innerHTML = this.faculty.map(f => `
          <tr>
            <td><strong>${f.employee_id}</strong></td>
            <td>${f.full_name}</td>
            <td>${f.designation}</td>
            <td>Dept #${f.department_id}</td>
            <td>${f.email}</td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.warn(e);
    }
  }

  // ==================== COURSES ====================
  async loadCourses() {
    try {
      const res = await fetch(`${API_BASE}/courses`);
      this.courses = res.ok ? await res.json() : [];
      const tbody = document.getElementById('coursesTableBody');
      if (tbody) {
        tbody.innerHTML = this.courses.map(c => {
          const prereqObj = c.prerequisite_id ? this.courses.find(x => x.id === c.prerequisite_id) : null;
          const prereqText = prereqObj ? `${prereqObj.code} (${prereqObj.title})` : (c.prerequisite_id ? `Course #${c.prerequisite_id}` : 'None');
          return `
            <tr>
              <td><strong>${c.code}</strong></td>
              <td>${c.title}</td>
              <td>${c.credits} Credits</td>
              <td>${c.max_capacity} Students</td>
              <td>Semester ${c.semester}</td>
              <td><span class="badge ${c.prerequisite_id ? 'badge-suspended' : 'badge-light'}">${prereqText}</span></td>
              <td><span class="badge ${c.is_active ? 'badge-active' : 'badge-suspended'}">${c.is_active ? 'Active' : 'Inactive'}</span></td>
            </tr>
          `;
        }).join('');
      }
    } catch (e) {
      console.warn(e);
    }
  }

  // ==================== EXAMINATIONS ====================
  async loadExams() {
    const tbody = document.getElementById('examsTableBody');
    if (!tbody) return;
    try {
      let allExams = [];
      for (const c of this.courses) {
        const res = await fetch(`${API_BASE}/examinations/course/${c.id}`);
        if (res.ok) {
          const list = await res.json();
          allExams = allExams.concat(list);
        }
      }
      this.exams = allExams;

      if (this.exams.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No scheduled examinations found.</td></tr>`;
        return;
      }

      tbody.innerHTML = this.exams.map(e => `
        <tr>
          <td><strong>${e.course_code || `Course #${e.course_id}`}</strong></td>
          <td>${e.title}</td>
          <td><span class="badge">${e.exam_type.toUpperCase()}</span></td>
          <td>${e.max_marks}</td>
          <td>${e.weightage_percent}%</td>
          <td>Sem ${e.semester}</td>
          <td>
            <button class="btn btn-sm btn-primary" onclick="app.openGradeExamDirectly(${e.id})">Enter Marks</button>
          </td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn(e);
    }
  }

  openGradeExamDirectly(examId) {
    this.openEnterGradeModal();
    const select = document.getElementById('grdExamSelect');
    if (select) select.value = examId;
  }

  openEnterGradeModal() {
    const examSelect = document.getElementById('grdExamSelect');
    const studentSelect = document.getElementById('grdStudentSelect');
    if (examSelect) {
      examSelect.innerHTML = this.exams.map(e => `<option value="${e.id}">${e.title} (Max: ${e.max_marks})</option>`).join('');
    }
    if (studentSelect) {
      studentSelect.innerHTML = this.students.map(s => `<option value="${s.id}">${s.register_number} — ${s.full_name}</option>`).join('');
    }
    this.openModal('gradeModal');
  }

  async handleGradeSubmit(e) {
    e.preventDefault();
    const examId = parseInt(document.getElementById('grdExamSelect').value, 10);
    const studentId = parseInt(document.getElementById('grdStudentSelect').value, 10);
    const marks = parseFloat(document.getElementById('grdMarks').value);
    const isAbsent = document.getElementById('grdAbsent').value === 'true';
    const reason = document.getElementById('grdReason').value.trim();

    try {
      const res = await fetch(`${API_BASE}/grades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          examination_id: examId,
          student_id: studentId,
          marks_obtained: marks,
          is_absent: isAbsent,
          remarks: reason || undefined
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to enter grade');

      this.showToast('Grade recorded successfully!', 'success');
      this.closeModal('gradeModal');
      this.refreshDashboard();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== FEE LEDGER ====================
  async loadFeeInvoices() {
    const tbody = document.getElementById('feesTableBody');
    if (!tbody) return;
    try {
      let allInvoices = [];
      for (const s of this.students.slice(0, 15)) {
        const res = await fetch(`${API_BASE}/fees/invoices/student/${s.id}`);
        if (res.ok) {
          const list = await res.json();
          allInvoices = allInvoices.concat(list);
        }
      }
      this.invoices = allInvoices;

      if (this.invoices.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No fee invoices recorded yet. Click "+ Generate Fee Invoice".</td></tr>`;
        return;
      }

      tbody.innerHTML = this.invoices.map(inv => `
        <tr>
          <td><strong>${inv.invoice_number}</strong></td>
          <td>${inv.student_reg || `Student #${inv.student_id}`}</td>
          <td>${inv.title}</td>
          <td>₹${inv.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
          <td>₹${inv.waiver_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
          <td>₹${(inv.amount - inv.waiver_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
          <td>${inv.due_date}</td>
          <td><span class="badge badge-${inv.status}">${inv.status}</span></td>
          <td>
            ${inv.balance_due > 0 ?
              `<button class="btn btn-sm btn-success" onclick="app.openPaymentModal(${inv.id}, '${inv.invoice_number}', ${inv.balance_due})">Pay (₹${inv.balance_due.toFixed(2)})</button>` :
              `<span class="badge badge-active">Fully Paid</span>`
            }
          </td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn(e);
    }
  }

  openPaymentModal(invoiceId, invoiceNumber, balanceDue) {
    document.getElementById('payInvoiceId').value = invoiceId;
    document.getElementById('payInvoiceNumber').value = invoiceNumber;
    document.getElementById('payCurrentBalance').value = `₹${balanceDue.toFixed(2)}`;
    document.getElementById('payAmount').value = balanceDue.toFixed(2);
    document.getElementById('payDate').value = new Date().toISOString().split('T')[0];
    this.openModal('paymentModal');
  }

  async handlePaymentSubmit(e) {
    e.preventDefault();
    const invId = parseInt(document.getElementById('payInvoiceId').value, 10);
    const amount = parseFloat(document.getElementById('payAmount').value);
    const method = document.getElementById('payMethod').value;
    const date = document.getElementById('payDate').value;

    try {
      const res = await fetch(`${API_BASE}/fees/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoice_id: invId,
          amount_paid: amount,
          payment_method: method,
          payment_date: date
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Payment could not be recorded');

      this.showToast(`Payment of ₹${amount.toFixed(2)} processed! Ref: ${data.payment_reference}`, 'success');
      this.closeModal('paymentModal');
      this.loadFeeInvoices();
      this.refreshDashboard();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  openCreateInvoiceModal() {
    const select = document.getElementById('invStudentSelect');
    if (select) {
      select.innerHTML = this.students.map(s => `<option value="${s.id}">${s.register_number} — ${s.full_name}</option>`).join('');
    }
    const due = document.getElementById('invDueDate');
    if (due && !due.value) {
      const d = new Date();
      d.setDate(d.getDate() + 30);
      due.value = d.toISOString().split('T')[0];
    }
    this.openModal('invoiceModal');
  }

  async handleInvoiceSubmit(e) {
    e.preventDefault();
    const payload = {
      student_id: parseInt(document.getElementById('invStudentSelect').value, 10),
      title: document.getElementById('invTitle').value.trim(),
      amount: parseFloat(document.getElementById('invAmount').value),
      waiver_amount: parseFloat(document.getElementById('invWaiver').value) || 0.0,
      due_date: document.getElementById('invDueDate').value
    };

    try {
      const res = await fetch(`${API_BASE}/fees/invoices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create invoice');

      this.showToast(`Invoice ${data.invoice_number} generated!`, 'success');
      this.closeModal('invoiceModal');
      this.loadFeeInvoices();
      this.refreshDashboard();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== TIMETABLE ====================
  async loadTimetable() {
    const tbody = document.getElementById('timetableSlotsBody');
    if (!tbody) return;
    try {
      const res = await fetch(`${API_BASE}/timetable/slots`);
      const slots = res.ok ? await res.json() : [];

      if (slots.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No timetable slots scheduled.</td></tr>`;
        return;
      }

      tbody.innerHTML = slots.map(s => `
        <tr>
          <td><strong>${s.day_of_week}</strong></td>
          <td>${s.start_time} - ${s.end_time}</td>
          <td>${s.course_code || `Course #${s.course_id}`} — ${s.course_title || ''}</td>
          <td>${s.faculty_name || `Faculty #${s.faculty_id}`}</td>
          <td>${s.room_number || `Hall #${s.classroom_id}`}</td>
          <td><span class="badge badge-active">Conflict Free</span></td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn(e);
    }
  }

  openScheduleSlotModal() {
    const cSelect = document.getElementById('slotCourseSelect');
    const fSelect = document.getElementById('slotFacultySelect');
    const rSelect = document.getElementById('slotRoomSelect');

    if (cSelect) cSelect.innerHTML = this.courses.map(c => `<option value="${c.id}">${c.code} — ${c.title}</option>`).join('');
    if (fSelect) fSelect.innerHTML = this.faculty.map(f => `<option value="${f.id}">${f.full_name} (${f.designation})</option>`).join('');
    
    // Fetch classrooms
    fetch(`${API_BASE}/timetable/classrooms`).then(r => r.json()).then(rooms => {
      if (rSelect) rSelect.innerHTML = rooms.map(rm => `<option value="${rm.id}">${rm.room_number} (${rm.building}, Cap: ${rm.capacity})</option>`).join('');
    });

    this.openModal('slotModal');
  }

  async handleSlotSubmit(e) {
    e.preventDefault();
    const payload = {
      course_id: parseInt(document.getElementById('slotCourseSelect').value, 10),
      faculty_id: parseInt(document.getElementById('slotFacultySelect').value, 10),
      classroom_id: parseInt(document.getElementById('slotRoomSelect').value, 10),
      day_of_week: document.getElementById('slotDay').value,
      start_time: document.getElementById('slotStart').value,
      end_time: document.getElementById('slotEnd').value,
      academic_year: '2026-2027',
      semester: 1
    };

    try {
      const res = await fetch(`${API_BASE}/timetable/slots`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Schedule conflict detected');

      this.showToast('Time slot successfully verified and scheduled!', 'success');
      this.closeModal('slotModal');
      this.loadTimetable();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== REPORTS & CSV ====================
  async loadReports() {
    const tbody = document.getElementById('reportsDeptBody');
    if (!tbody) return;
    try {
      const res = await fetch(`${API_BASE}/analytics/departments`);
      const data = res.ok ? await res.json() : [];

      tbody.innerHTML = data.map(d => `
        <tr>
          <td><strong>${d.department}</strong></td>
          <td>${d.student_count}</td>
          <td>${d.average_gpa.toFixed(2)}</td>
          <td>${d.attendance_rate.toFixed(1)}%</td>
          <td>
            <span class="badge ${d.attendance_rate >= 75 ? 'badge-active' : 'badge-suspended'}">
              ${d.attendance_rate >= 75 ? 'Good Standing' : 'Attendance Alert'}
            </span>
          </td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn(e);
    }
  }

  exportStudentsCSV() {
    window.location.href = `${API_BASE}/reports/export/students`;
    this.showToast('Generating safe CSV export...', 'success');
  }

  exportFeesCSV() {
    window.location.href = `${API_BASE}/reports/export/fees`;
    this.showToast('Generating fee ledger export...', 'success');
  }

  // ==================== AUDIT LOGS ====================
  async loadAuditLogs() {
    const tbody = document.getElementById('auditTableBody');
    if (!tbody) return;
    try {
      const res = await fetch(`${API_BASE}/audit?limit=50`);
      const logs = res.ok ? await res.json() : [];

      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No audit entries recorded yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = logs.map(l => `
        <tr>
          <td><small>${new Date(l.timestamp).toLocaleString()}</small></td>
          <td><span class="badge badge-active">${l.action}</span></td>
          <td>${l.entity_type}</td>
          <td>#${l.entity_id || 'N/A'}</td>
          <td><strong>${l.username || 'System'}</strong></td>
          <td><small>${l.new_values || l.old_values || 'N/A'}</small></td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn(e);
    }
  }

  // ==================== VALIDATION & FORM UTILITIES ====================
  autoGenRegNumber(targetInputId) {
    const el = document.getElementById(targetInputId);
    if (!el) return;
    const year = new Date().getFullYear();
    const rand = Math.floor(1000 + Math.random() * 9000);
    el.value = `REG${year}${rand}`;
    el.dispatchEvent(new Event('input'));
  }

  isValidEmail(email) {
    if (!email) return false;
    return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email.trim());
  }

  isValid10DigitPhone(phone) {
    if (!phone) return false;
    const clean = phone.replace(/\D/g, '');
    return clean.length === 10;
  }

  formatApiError(data, fallbackMsg) {
    if (!data) return fallbackMsg;
    if (data.detail) {
      if (Array.isArray(data.detail)) {
        return data.detail.map(e => `${e.loc ? e.loc[e.loc.length - 1] + ': ' : ''}${e.msg}`).join(', ');
      }
      if (typeof data.detail === 'string') return data.detail;
    }
    if (data.message) return data.message;
    return fallbackMsg;
  }

  setupPhoneInput(inputId, counterId, errorId) {
    const input = document.getElementById(inputId);
    const counter = document.getElementById(counterId);
    const err = document.getElementById(errorId);
    if (!input) return;

    input.addEventListener('input', () => {
      let val = input.value.replace(/\D/g, '');
      if (val.length > 10) val = val.slice(0, 10);
      input.value = val;

      if (counter) {
        counter.textContent = `${val.length}/10 digits`;
        if (val.length === 10) {
          counter.classList.add('valid');
          if (err) err.textContent = '';
        } else {
          counter.classList.remove('valid');
        }
      }
    });

    input.addEventListener('blur', () => {
      const val = input.value.replace(/\D/g, '');
      if (err) {
        if (!val) {
          err.textContent = 'Phone number is required.';
        } else if (val.length !== 10) {
          err.textContent = `Phone number must be exactly 10 digits (currently ${val.length}).`;
        } else {
          err.textContent = '';
        }
      }
    });
  }

  setupEmailInput(inputId, errorId) {
    const input = document.getElementById(inputId);
    const err = document.getElementById(errorId);
    if (!input) return;

    input.addEventListener('input', () => {
      if (err && this.isValidEmail(input.value)) {
        err.textContent = '';
      }
    });

    input.addEventListener('blur', () => {
      if (err) {
        const val = input.value.trim();
        if (!val) {
          err.textContent = 'Email address is required.';
        } else if (!this.isValidEmail(val)) {
          err.textContent = 'Please enter a valid email format (e.g. name@university.edu).';
        } else {
          err.textContent = '';
        }
      }
    });
  }

  // ==================== QUICK ADD STUDENT MODAL ====================
  openAddStudentModal() {
    const form = document.getElementById('quickAddStudentForm');
    if (form) form.reset();
    const regInput = document.getElementById('qckRegNumber');
    if (regInput && !regInput.value) {
      this.autoGenRegNumber('qckRegNumber');
    }
    const counter = document.getElementById('qckPhoneCounter');
    if (counter) {
      counter.textContent = '0/10 digits';
      counter.classList.remove('valid');
    }
    ['errQckFullName', 'errQckRegNumber', 'errQckEmail', 'errQckPhone'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    this.openModal('addStudentModal');
  }

  async handleQuickAddStudentSubmit(e) {
    e.preventDefault();
    const fullName = document.getElementById('qckFullName').value.trim();
    const regNumber = document.getElementById('qckRegNumber').value.trim();
    const email = document.getElementById('qckEmail').value.trim();
    const phone = document.getElementById('qckPhone').value.trim();
    const dept = document.getElementById('qckDepartment').value;
    const year = document.getElementById('qckAcademicYear').value;
    const semester = parseInt(document.getElementById('qckSemester').value, 10) || 1;
    const status = document.getElementById('qckStatus').value;
    const gpa = parseFloat(document.getElementById('qckGpa').value) || 0.0;
    const dob = document.getElementById('qckDob').value || undefined;

    let hasErr = false;
    if (!fullName || fullName.length < 2) {
      document.getElementById('errQckFullName').textContent = 'Full name must be at least 2 characters.';
      hasErr = true;
    } else {
      document.getElementById('errQckFullName').textContent = '';
    }

    if (!regNumber || regNumber.length < 2) {
      document.getElementById('errQckRegNumber').textContent = 'Registration number is required.';
      hasErr = true;
    } else {
      document.getElementById('errQckRegNumber').textContent = '';
    }

    if (!this.isValidEmail(email)) {
      document.getElementById('errQckEmail').textContent = 'Please enter a valid email format (e.g. name@university.edu).';
      hasErr = true;
    } else {
      document.getElementById('errQckEmail').textContent = '';
    }

    const cleanPhone = phone.replace(/\D/g, '');
    if (cleanPhone.length !== 10) {
      document.getElementById('errQckPhone').textContent = 'Phone number must be exactly 10 digits (e.g. 9876543210).';
      hasErr = true;
    } else {
      document.getElementById('errQckPhone').textContent = '';
    }

    if (hasErr) return;

    const payload = {
      full_name: fullName,
      register_number: regNumber,
      email: email,
      phone_number: cleanPhone,
      department: dept,
      academic_year: year,
      semester: semester,
      status: status,
      gpa: gpa,
      date_of_birth: dob
    };

    const submitBtn = document.getElementById('qckSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving Student...';

    try {
      const res = await fetch('/students', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(this.formatApiError(data, 'Failed to add student'));
      }

      this.closeModal('addStudentModal');
      this.showToast(`Student ${data.full_name} (${data.register_number}) created successfully!`, 'success');
      await this.loadStudents();
      this.refreshDashboard();
      this.switchTab('students');
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '✓ Save & Add Student';
    }
  }

  // ==================== EDIT STUDENT MODAL ====================
  async openEditStudentModal(studentId) {
    const s = this.studentsList.find(item => item.id === studentId);
    if (!s) {
      this.showToast('Student record not found.', 'error');
      return;
    }

    document.getElementById('editStudentId').value = s.id;
    document.getElementById('editFullName').value = s.full_name || '';
    document.getElementById('editRegNumber').value = s.register_number || '';
    document.getElementById('editEmail').value = s.email || '';
    const cleanPhone = (s.phone_number || '').replace(/\D/g, '').slice(0, 10);
    document.getElementById('editPhone').value = cleanPhone;
    const counter = document.getElementById('editPhoneCounter');
    if (counter) {
      counter.textContent = `${cleanPhone.length}/10 digits`;
      if (cleanPhone.length === 10) counter.classList.add('valid');
      else counter.classList.remove('valid');
    }
    document.getElementById('editDepartment').value = s.department || 'Computer Science';
    document.getElementById('editAcademicYear').value = s.academic_year || '1st Year';
    document.getElementById('editSemester').value = s.semester || 1;
    document.getElementById('editStatus').value = s.status || 'active';
    document.getElementById('editGpa').value = (s.gpa !== undefined && s.gpa !== null) ? s.gpa : 0.0;

    ['errEditFullName', 'errEditEmail', 'errEditPhone'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });

    this.openModal('editStudentModal');
  }

  async handleEditStudentSubmit(e) {
    e.preventDefault();
    const studentId = document.getElementById('editStudentId').value;
    const fullName = document.getElementById('editFullName').value.trim();
    const email = document.getElementById('editEmail').value.trim();
    const phone = document.getElementById('editPhone').value.trim();
    const dept = document.getElementById('editDepartment').value;
    const year = document.getElementById('editAcademicYear').value;
    const semester = parseInt(document.getElementById('editSemester').value, 10) || 1;
    const status = document.getElementById('editStatus').value;
    const gpa = parseFloat(document.getElementById('editGpa').value) || 0.0;

    let hasErr = false;
    if (!fullName || fullName.length < 2) {
      document.getElementById('errEditFullName').textContent = 'Full name must be at least 2 characters.';
      hasErr = true;
    } else {
      document.getElementById('errEditFullName').textContent = '';
    }

    if (!this.isValidEmail(email)) {
      document.getElementById('errEditEmail').textContent = 'Please enter a valid email format.';
      hasErr = true;
    } else {
      document.getElementById('errEditEmail').textContent = '';
    }

    const cleanPhone = phone.replace(/\D/g, '');
    if (cleanPhone.length !== 10) {
      document.getElementById('errEditPhone').textContent = 'Phone number must be exactly 10 digits.';
      hasErr = true;
    } else {
      document.getElementById('errEditPhone').textContent = '';
    }

    if (hasErr) return;

    const payload = {
      full_name: fullName,
      email: email,
      phone_number: cleanPhone,
      department: dept,
      academic_year: year,
      semester: semester,
      status: status,
      gpa: gpa
    };

    const submitBtn = document.getElementById('editSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    try {
      const res = await fetch(`/students/${studentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(this.formatApiError(data, 'Failed to update student'));
      }

      this.closeModal('editStudentModal');
      this.showToast(`Student ${data.full_name} updated successfully!`, 'success');
      await this.loadStudents();
      this.refreshDashboard();
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Save Changes';
    }
  }

  // ==================== DEPARTMENT MODAL ====================
  openAddDeptModal() {
    const f = document.getElementById('deptForm');
    if (f) f.reset();
    ['errDeptCode', 'errDeptName'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    this.openModal('deptModal');
  }

  async handleDeptSubmit(e) {
    e.preventDefault();
    const code = document.getElementById('deptCode').value.trim();
    const name = document.getElementById('deptName').value.trim();
    const hod = document.getElementById('deptHod').value.trim() || undefined;
    const building = document.getElementById('deptBuilding').value.trim() || undefined;
    const budget = parseFloat(document.getElementById('deptBudget').value) || 0;

    let hasErr = false;
    if (!code || code.length < 2) {
      document.getElementById('errDeptCode').textContent = 'Code is required (min 2 chars).';
      hasErr = true;
    } else {
      document.getElementById('errDeptCode').textContent = '';
    }
    if (!name || name.length < 2) {
      document.getElementById('errDeptName').textContent = 'Name is required (min 2 chars).';
      hasErr = true;
    } else {
      document.getElementById('errDeptName').textContent = '';
    }
    if (hasErr) return;

    try {
      const res = await fetch('/api/v1/departments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, name, head_of_department: hod, building, budget })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(this.formatApiError(data, 'Failed to create department'));

      this.closeModal('deptModal');
      this.showToast(`Department ${data.name} (${data.code}) created!`, 'success');
      await this.loadDepartmentsAndFaculty();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== FACULTY MODAL ====================
  openAddFacultyModal() {
    const f = document.getElementById('facultyForm');
    if (f) f.reset();
    const sel = document.getElementById('facDeptSelect');
    if (sel) {
      sel.innerHTML = this.departments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    }
    const counter = document.getElementById('facPhoneCounter');
    if (counter) {
      counter.textContent = '0/10 digits';
      counter.classList.remove('valid');
    }
    ['errFacEmployeeId', 'errFacFullName', 'errFacEmail', 'errFacPhone'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    this.openModal('facultyModal');
  }

  async handleFacultySubmit(e) {
    e.preventDefault();
    const empId = document.getElementById('facEmployeeId').value.trim();
    const name = document.getElementById('facFullName').value.trim();
    const email = document.getElementById('facEmail').value.trim();
    const phone = document.getElementById('facPhone').value.trim();
    const deptId = parseInt(document.getElementById('facDeptSelect').value, 10);
    const designation = document.getElementById('facDesignation').value;
    const spec = document.getElementById('facSpecialization').value.trim() || undefined;

    let hasErr = false;
    if (!empId) {
      document.getElementById('errFacEmployeeId').textContent = 'Employee ID is required.';
      hasErr = true;
    } else {
      document.getElementById('errFacEmployeeId').textContent = '';
    }
    if (!name) {
      document.getElementById('errFacFullName').textContent = 'Full name is required.';
      hasErr = true;
    } else {
      document.getElementById('errFacFullName').textContent = '';
    }
    if (!this.isValidEmail(email)) {
      document.getElementById('errFacEmail').textContent = 'Valid email is required.';
      hasErr = true;
    } else {
      document.getElementById('errFacEmail').textContent = '';
    }
    const cleanPhone = phone.replace(/\D/g, '');
    if (cleanPhone && cleanPhone.length !== 10) {
      document.getElementById('errFacPhone').textContent = 'Phone number must be exactly 10 digits.';
      hasErr = true;
    } else {
      document.getElementById('errFacPhone').textContent = '';
    }
    if (hasErr) return;

    try {
      const res = await fetch('/api/v1/faculty', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: empId,
          full_name: name,
          email: email,
          phone_number: cleanPhone || undefined,
          department_id: deptId,
          designation: designation,
          specialization: spec
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(this.formatApiError(data, 'Failed to create faculty member'));

      this.closeModal('facultyModal');
      this.showToast(`Faculty member ${data.full_name} added!`, 'success');
      await this.loadDepartmentsAndFaculty();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== COURSE MODAL ====================
  async openAddCourseModal() {
    const f = document.getElementById('courseForm');
    if (f) f.reset();

    // Ensure departments and courses catalog are loaded
    if (!this.departments || this.departments.length === 0) {
      await this.loadDepartmentsAndFaculty();
    }
    if (!this.courses || this.courses.length === 0) {
      await this.loadCourses();
    }

    const sel = document.getElementById('crsDeptSelect');
    if (sel) {
      if (this.departments.length === 0) {
        sel.innerHTML = '<option value="">-- No Departments Available (Create a department first) --</option>';
      } else {
        sel.innerHTML = this.departments.map(d => `<option value="${d.id}">${d.name} (${d.code})</option>`).join('');
      }
    }

    const prereqSel = document.getElementById('crsPrereqSelect');
    if (prereqSel) {
      prereqSel.innerHTML = '<option value="">-- None (No Prerequisite) --</option>' +
        this.courses.filter(c => c.is_active).map(c => `<option value="${c.id}">${c.code} — ${c.title}</option>`).join('');
    }

    ['errCrsCode', 'errCrsTitle', 'errCrsDept', 'errCrsPrereq'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    this.openModal('courseModal');
  }

  async handleCourseSubmit(e) {
    e.preventDefault();
    const code = document.getElementById('crsCode').value.trim();
    const title = document.getElementById('crsTitle').value.trim();
    const deptVal = document.getElementById('crsDeptSelect').value;
    const deptId = parseInt(deptVal, 10);
    const credits = parseInt(document.getElementById('crsCredits').value, 10) || 3;
    const capacity = parseInt(document.getElementById('crsCapacity').value, 10) || 60;
    const semester = parseInt(document.getElementById('crsSemester').value, 10) || 1;
    const desc = document.getElementById('crsDesc').value.trim() || undefined;
    const prereqVal = document.getElementById('crsPrereqSelect')?.value;
    const prereqId = prereqVal ? parseInt(prereqVal, 10) : undefined;

    let hasErr = false;
    if (!code) {
      document.getElementById('errCrsCode').textContent = 'Course code is required.';
      hasErr = true;
    } else {
      document.getElementById('errCrsCode').textContent = '';
    }
    if (!title) {
      document.getElementById('errCrsTitle').textContent = 'Course title is required.';
      hasErr = true;
    } else {
      document.getElementById('errCrsTitle').textContent = '';
    }
    if (isNaN(deptId) || !deptVal) {
      const el = document.getElementById('errCrsDept');
      if (el) el.textContent = 'A valid academic department must be selected.';
      hasErr = true;
    } else {
      const el = document.getElementById('errCrsDept');
      if (el) el.textContent = '';
    }
    if (hasErr) return;

    try {
      const res = await fetch('/api/v1/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: code,
          title: title,
          department_id: deptId,
          credits: credits,
          max_capacity: capacity,
          semester: semester,
          description: desc,
          prerequisite_id: prereqId
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(this.formatApiError(data, 'Failed to create course'));

      this.closeModal('courseModal');
      this.showToast(`Course ${data.code} — ${data.title} successfully created!`, 'success');
      await this.loadCourses();
    } catch (err) {
      this.showToast(err.message, 'error');
      const prereqErr = document.getElementById('errCrsPrereq');
      if (prereqErr && err.message.toLowerCase().includes('prerequisite')) {
        prereqErr.textContent = err.message;
      }
    }
  }

  // ==================== HOD APPOINTMENT MODAL ====================
  openAssignHodModal(deptId) {
    const dept = this.departments.find(d => d.id === deptId);
    if (!dept) return;

    document.getElementById('hodDeptId').value = deptId;
    document.getElementById('hodDeptName').value = `${dept.name} (${dept.code})`;

    // Filter faculty belonging to this department who are active
    const deptFaculty = this.faculty.filter(f => f.department_id === deptId && f.is_active);
    const sel = document.getElementById('hodFacultySelect');
    const errEl = document.getElementById('errHodFaculty');
    if (errEl) errEl.textContent = '';

    if (deptFaculty.length === 0) {
      sel.innerHTML = '<option value="">-- No Active Faculty Members Assigned to this Department --</option>';
    } else {
      sel.innerHTML = deptFaculty.map(f => `
        <option value="${f.id}" ${f.id === dept.hod_faculty_id ? 'selected' : ''}>
          ${f.full_name} (${f.designation} — ${f.employee_id})
        </option>
      `).join('');
    }

    const vacateBtn = document.getElementById('vacateHodBtn');
    if (vacateBtn) {
      vacateBtn.style.display = dept.hod_faculty_id ? 'inline-block' : 'none';
    }

    this.openModal('assignHodModal');
  }

  async handleAssignHodSubmit(e) {
    e.preventDefault();
    const deptId = parseInt(document.getElementById('hodDeptId').value, 10);
    const facVal = document.getElementById('hodFacultySelect').value;
    const facId = parseInt(facVal, 10);

    const errEl = document.getElementById('errHodFaculty');
    if (isNaN(facId) || !facVal) {
      if (errEl) errEl.textContent = 'Please select an eligible faculty member.';
      return;
    }
    if (errEl) errEl.textContent = '';

    try {
      const res = await fetch(`/api/v1/departments/${deptId}/hod`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ faculty_id: facId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(this.formatApiError(data, 'Failed to assign Head of Department'));

      this.closeModal('assignHodModal');
      this.showToast(`Appointed ${data.head_of_department} as Head of Department!`, 'success');
      await this.loadDepartmentsAndFaculty();
    } catch (err) {
      this.showToast(err.message, 'error');
      if (errEl) errEl.textContent = err.message;
    }
  }

  async handleVacateHod() {
    const deptId = parseInt(document.getElementById('hodDeptId').value, 10);
    if (!deptId) return;

    try {
      const res = await fetch(`/api/v1/departments/${deptId}/hod`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(this.formatApiError(data, 'Failed to vacate Head of Department'));

      this.closeModal('assignHodModal');
      this.showToast(`Head of Department role vacated for ${data.name}.`, 'info');
      await this.loadDepartmentsAndFaculty();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== EXAMINATION MODAL ====================
  openCreateExamModal() {
    const f = document.getElementById('examScheduleForm');
    if (f) f.reset();
    const sel = document.getElementById('exmCourseSelect');
    if (sel) {
      sel.innerHTML = this.courses.map(c => `<option value="${c.id}">${c.code} — ${c.title}</option>`).join('');
    }
    ['errExmCourse', 'errExmTitle'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    this.openModal('examModal');
  }

  async handleExamSubmit(e) {
    e.preventDefault();
    const courseId = parseInt(document.getElementById('exmCourseSelect').value, 10);
    const title = document.getElementById('exmTitle').value.trim();
    const examType = document.getElementById('exmType').value;
    const maxMarks = parseFloat(document.getElementById('exmMaxMarks').value) || 100.0;
    const weightage = parseFloat(document.getElementById('exmWeightage').value) || 30.0;
    const examDate = document.getElementById('exmDate').value || undefined;

    let hasErr = false;
    if (!courseId) {
      document.getElementById('errExmCourse').textContent = 'Please select a course.';
      hasErr = true;
    } else {
      document.getElementById('errExmCourse').textContent = '';
    }
    if (!title) {
      document.getElementById('errExmTitle').textContent = 'Examination title is required.';
      hasErr = true;
    } else {
      document.getElementById('errExmTitle').textContent = '';
    }
    if (hasErr) return;

    try {
      const res = await fetch('/api/v1/examinations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: courseId,
          title: title,
          exam_type: examType,
          max_marks: maxMarks,
          weightage_percent: weightage,
          exam_date: examDate
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(this.formatApiError(data, 'Failed to schedule exam'));

      this.closeModal('examModal');
      this.showToast(`Exam "${data.title}" scheduled successfully!`, 'success');
      await this.loadExaminationsAndGrades();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== CLASSROOM MODAL ====================
  openAddClassroomModal() {
    const f = document.getElementById('classroomForm');
    if (f) f.reset();
    ['errClsRoomNum', 'errClsBuilding'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    this.openModal('classroomModal');
  }

  async handleClassroomSubmit(e) {
    e.preventDefault();
    const roomNum = document.getElementById('clsRoomNum').value.trim();
    const building = document.getElementById('clsBuilding').value.trim();
    const roomType = document.getElementById('clsRoomType').value;
    const capacity = parseInt(document.getElementById('clsCapacity').value, 10) || 60;

    let hasErr = false;
    if (!roomNum) {
      document.getElementById('errClsRoomNum').textContent = 'Room number is required.';
      hasErr = true;
    } else {
      document.getElementById('errClsRoomNum').textContent = '';
    }
    if (!building) {
      document.getElementById('errClsBuilding').textContent = 'Building name is required.';
      hasErr = true;
    } else {
      document.getElementById('errClsBuilding').textContent = '';
    }
    if (hasErr) return;

    try {
      const res = await fetch('/api/v1/timetable/classrooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_number: roomNum,
          building: building,
          room_type: roomType,
          capacity: capacity
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(this.formatApiError(data, 'Failed to add classroom'));

      this.closeModal('classroomModal');
      this.showToast(`Classroom ${data.room_number} added!`, 'success');
      await this.loadTimetableAndClassrooms();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ==================== DEMO DATA SEEDING ====================
  async seedDemoData() {
    const btn = document.getElementById('quickSeedBtn');
    if (btn) btn.disabled = true;
    this.showToast('Seeding realistic student records...', 'warning');

    const sampleStudents = [
      { full_name: "Eleanor Vance", register_number: "CS2026001", email: "eleanor.vance@university.edu", phone_number: "9876543201", department: "Computer Science", academic_year: "1st Year", semester: 1, status: "active", gpa: 3.85 },
      { full_name: "Marcus Aurelius", register_number: "CS2026002", email: "marcus.a@university.edu", phone_number: "9876543202", department: "Computer Science", academic_year: "2nd Year", semester: 3, status: "active", gpa: 3.90 },
      { full_name: "Ada Lovelace", register_number: "IT2026001", email: "ada.lovelace@university.edu", phone_number: "9876543203", department: "Information Technology", academic_year: "3rd Year", semester: 5, status: "active", gpa: 4.00 },
      { full_name: "Nikola Tesla", register_number: "ECE2026001", email: "nikola.tesla@university.edu", phone_number: "9876543204", department: "Electronics & Communication", academic_year: "4th Year", semester: 7, status: "active", gpa: 3.75 },
      { full_name: "Leonardo DaVinci", register_number: "MECH2026001", email: "leonardo@university.edu", phone_number: "9876543205", department: "Mechanical Engineering", academic_year: "2nd Year", semester: 3, status: "active", gpa: 3.65 },
      { full_name: "Marie Curie", register_number: "CIVIL2026001", email: "marie.curie@university.edu", phone_number: "9876543206", department: "Civil Engineering", academic_year: "1st Year", semester: 1, status: "active", gpa: 3.95 }
    ];

    for (const s of sampleStudents) {
      try {
        await fetch('/students', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(s)
        });
      } catch (e) {
        // ignore duplicate errors during demo seeding
      }
    }

    await this.refreshAllData();
    this.showToast('Sample dataset loaded successfully!', 'success');
    if (btn) btn.disabled = false;
  }

  // ==================== AUTHENTICATION HELPER ====================
  async getAuthToken() {
    let token = localStorage.getItem('edutrack_token');
    if (!token) {
      try {
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'admin', password: 'AdminPass123!' })
        });
        if (res.ok) {
          const data = await res.json();
          token = data.access_token;
          localStorage.setItem('edutrack_token', token);
        }
      } catch (e) {
        console.warn('Could not acquire admin token', e);
      }
    }
    return token;
  }

  // ==================== CSV BULK IMPORT ====================
  openCSVImportModal() {
    this.resetCSVModal();
    this.openModal('csvImportModal');
  }

  resetCSVModal() {
    this.csvSelectedFile = null;
    this.csvPreviewData = null;

    const fileInput = document.getElementById('csvFileInput');
    if (fileInput) fileInput.value = '';

    const nameEl = document.getElementById('csvSelectedFileName');
    if (nameEl) {
      nameEl.textContent = '';
      nameEl.style.display = 'none';
    }

    // Reset Steps
    const upView = document.getElementById('csvUploadView');
    const prevView = document.getElementById('csvPreviewView');
    const resView = document.getElementById('csvResultView');
    if (upView) upView.style.display = 'block';
    if (prevView) prevView.style.display = 'none';
    if (resView) resView.style.display = 'none';

    const p1 = document.getElementById('csvStepPill1');
    const p2 = document.getElementById('csvStepPill2');
    const p3 = document.getElementById('csvStepPill3');
    if (p1) p1.className = 'step active';
    if (p2) p2.className = 'step';
    if (p3) p3.className = 'step';

    // Buttons
    const inspectBtn = document.getElementById('csvInspectBtn');
    const backBtn = document.getElementById('csvBackBtn');
    const confirmBtn = document.getElementById('csvConfirmImportBtn');
    const doneBtn = document.getElementById('csvDoneBtn');
    const errBtn = document.getElementById('csvDownloadErrorsBtn');

    if (inspectBtn) {
      inspectBtn.style.display = 'inline-flex';
      inspectBtn.disabled = false;
      inspectBtn.textContent = 'Inspect & Validate File →';
    }
    if (backBtn) backBtn.style.display = 'none';
    if (confirmBtn) confirmBtn.style.display = 'none';
    if (doneBtn) doneBtn.style.display = 'none';
    if (errBtn) errBtn.style.display = 'none';
  }

  handleCSVFileSelected(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      this.showToast('Please select a valid .csv file.', 'error');
      event.target.value = '';
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.showToast('File size exceeds 5MB limit.', 'error');
      event.target.value = '';
      return;
    }

    this.csvSelectedFile = file;
    const nameEl = document.getElementById('csvSelectedFileName');
    if (nameEl) {
      nameEl.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      nameEl.style.display = 'block';
    }
  }

  setupCSVDragAndDrop() {
    const dropzone = document.getElementById('csvDropzone');
    if (!dropzone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        const file = files[0];
        const dummyEvent = { target: { files: [file], value: '' } };
        this.handleCSVFileSelected(dummyEvent);
      }
    });
  }

  downloadCSVTemplate() {
    window.location.href = '/api/v1/students/csv-template';
  }

  async inspectCSVFile() {
    if (!this.csvSelectedFile) {
      this.showToast('Please choose or drag a CSV file first.', 'warning');
      return;
    }

    const inspectBtn = document.getElementById('csvInspectBtn');
    inspectBtn.disabled = true;
    inspectBtn.textContent = 'Inspecting CSV...';

    const token = await this.getAuthToken();
    const formData = new FormData();
    formData.append('file', this.csvSelectedFile);

    try {
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/students/import-csv/preview', {
        method: 'POST',
        headers: headers,
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(this.formatApiError(data, 'CSV inspection failed'));
      }

      this.csvPreviewData = data;

      // Update KPI Badges
      document.getElementById('prevTotalRows').textContent = data.total_rows;
      document.getElementById('prevValidRows').textContent = data.valid_rows_count;
      document.getElementById('prevDuplicateRows').textContent = data.duplicate_rows_count;
      document.getElementById('prevInvalidRows').textContent = data.invalid_rows_count;

      // Render Preview Table
      const tbody = document.getElementById('csvPreviewTableBody');
      if (data.preview_rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-3 text-muted">No records detected in file.</td></tr>';
      } else {
        tbody.innerHTML = data.preview_rows.map(r => {
          let badgeHtml = '<span class="badge badge-success">✓ Ready</span>';
          let errorText = '';

          if (!r.is_valid) {
            badgeHtml = `<span class="badge badge-danger">✕ Error</span>`;
            errorText = `<div class="text-danger small mt-1">${r.errors.join('<br>')}</div>`;
          } else if (r.is_duplicate) {
            badgeHtml = `<span class="badge badge-warning">⚠ Duplicate</span>`;
            errorText = `<div class="text-warning small mt-1">${r.duplicate_reason || 'Duplicate record'}</div>`;
          }

          return `
            <tr>
              <td><strong>${r.row_number}</strong></td>
              <td><code>${r.register_number}</code></td>
              <td>${r.full_name}</td>
              <td>${r.email}</td>
              <td>${r.phone_number}</td>
              <td>${r.department}</td>
              <td>${r.academic_year} / Sem ${r.semester}</td>
              <td>${r.status}</td>
              <td>${badgeHtml}${errorText}</td>
            </tr>
          `;
        }).join('');
      }

      // Show error download button if invalid rows exist
      const errBtn = document.getElementById('csvDownloadErrorsBtn');
      if (errBtn) {
        errBtn.style.display = data.error_summary && data.error_summary.length > 0 ? 'inline-flex' : 'none';
      }

      // Switch to Step 2
      document.getElementById('csvUploadView').style.display = 'none';
      document.getElementById('csvPreviewView').style.display = 'block';

      document.getElementById('csvStepPill1').className = 'step completed';
      document.getElementById('csvStepPill2').className = 'step active';

      inspectBtn.style.display = 'none';
      document.getElementById('csvBackBtn').style.display = 'inline-flex';
      const confirmBtn = document.getElementById('csvConfirmImportBtn');
      confirmBtn.style.display = 'inline-flex';
      confirmBtn.textContent = `✓ Import ${data.valid_rows_count} Valid Student(s)`;
      confirmBtn.disabled = data.valid_rows_count === 0;

    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      inspectBtn.disabled = false;
      inspectBtn.textContent = 'Inspect & Validate File →';
    }
  }

  backToCSVUpload() {
    document.getElementById('csvUploadView').style.display = 'block';
    document.getElementById('csvPreviewView').style.display = 'none';
    document.getElementById('csvStepPill1').className = 'step active';
    document.getElementById('csvStepPill2').className = 'step';

    document.getElementById('csvInspectBtn').style.display = 'inline-flex';
    document.getElementById('csvBackBtn').style.display = 'none';
    document.getElementById('csvConfirmImportBtn').style.display = 'none';
  }

  async downloadCSVErrorReport() {
    if (!this.csvPreviewData || !this.csvPreviewData.error_summary || this.csvPreviewData.error_summary.length === 0) {
      this.showToast('No errors to export.', 'info');
      return;
    }

    const token = await this.getAuthToken();
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/students/import-csv/error-report', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ errors: this.csvPreviewData.error_summary })
      });

      if (!res.ok) throw new Error('Failed to generate error report.');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'student_import_errors.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      this.showToast('Error report downloaded safely.', 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  async executeCSVImport() {
    if (!this.csvSelectedFile) {
      this.showToast('No file selected for import.', 'error');
      return;
    }

    const confirmBtn = document.getElementById('csvConfirmImportBtn');
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Importing Records...';

    const allowPartial = document.getElementById('csvAllowPartial').checked;
    const token = await this.getAuthToken();

    const formData = new FormData();
    formData.append('file', this.csvSelectedFile);
    formData.append('allow_partial', allowPartial);

    try {
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/students/import-csv', {
        method: 'POST',
        headers: headers,
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(this.formatApiError(data, 'Bulk import execution failed'));
      }

      // Populate Step 3
      document.getElementById('resImportedCount').textContent = data.imported_count;
      document.getElementById('resDuplicateCount').textContent = data.duplicate_count;
      document.getElementById('resFailedCount').textContent = data.failed_count;

      document.getElementById('csvPreviewView').style.display = 'none';
      document.getElementById('csvResultView').style.display = 'block';

      document.getElementById('csvStepPill2').className = 'step completed';
      document.getElementById('csvStepPill3').className = 'step active';

      document.getElementById('csvBackBtn').style.display = 'none';
      confirmBtn.style.display = 'none';
      document.getElementById('csvDoneBtn').style.display = 'inline-flex';

      this.showToast(`Bulk import completed: ${data.imported_count} students added!`, 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
      confirmBtn.disabled = false;
      confirmBtn.textContent = '✓ Import Valid Records Now';
    }
  }

  async closeCSVModalAndRefresh() {
    this.closeModal('csvImportModal');
    await this.loadStudents();
    this.refreshDashboard();
    this.switchTab('students');
  }

  // ==================== MODALS & TOASTS ====================
  openModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.add('open');
  }

  closeModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove('open');
  }

  showToast(message, type = 'info') {
    const stack = document.getElementById('toastStack');
    if (!stack) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `<span><strong>${icon}</strong></span><span>${message}</span>`;

    stack.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }
}

// Global Application Instance
let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new EduTrackApp();
  window.app = app;
});
