class SMChart:
    """Represents a parsed StepMania chart"""
    
    def __init__(self, metadata, steps):
        self.metadata = metadata
        self.steps = steps  # List of Step objects
        
    def get_bpm(self):
        """Get the BPM for timing calculations"""
        return self.metadata.get('bpm', 120.0)
    
    def get_title(self):
        """Get song title"""
        return self.metadata.get('title', 'Unknown')
        
    def get_steps_count(self):
        """Get total number of steps in chart"""
        return len(self.steps)

class Step:
    """Represents a single step/note in the chart"""
    
    def __init__(self, time_ms, lane, note_type=1):
        self.time_ms = time_ms      # When the step should be hit (milliseconds)
        self.lane = lane            # 0=Left, 1=Down, 2=Up, 3=Right
        self.note_type = note_type  # 1=normal, 2=hold_start, 3=hold_end
        self.hit = False            # Whether this step has been hit
        self.visible = False        # Whether this step is currently visible
    
    def __repr__(self):
        lane_names = ['Left', 'Down', 'Up', 'Right']
        return f"Step({self.time_ms}ms, {lane_names[self.lane]}, type={self.note_type})"

class SMParser:
    def __init__(self):
        self.difficulties = {
            "beginner": "Beginner",
            "easy"    : "Easy", 
            "medium"  : "Medium",
            "hard"    : "Hard",
        }

    def parse_file(self, filepath, difficulty='beginner'):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

        # Get required metadata from sm file
        metadata = self._parse_metadata(content)
        print(metadata)

        steps = self._parse_steps(content, difficulty, metadata.get('bpm', 120.0))

        # return SMChart(metadata, steps)

    def _parse_metadata(self, content):

        metadata = {}
        metadata["title"]  = self._extract_field(content, "TITLE")
        metadata["artist"] = self._extract_field(content, "ARTIST")
        metadata["music"]  = self._extract_field(content, "MUSIC")

        bpm_str = self._extract_field(content, "BPMS")
        if bpm_str:
            try:
                if '=' in bpm_str:
                    metadata["bpm"] = float(bpm_str.split('=')[1])
                else:
                    metadata["bpm"] = float(bpm_str)
            except (ValueError, IndexError) as e:
                print(f"BPM could not be read from sm file, returned the following Exception: {e}\n - setting BPM to the default value of 120.0")
                metadata['bpm'] = 120.0
        else:
            print(f"BPM could not be found in sm file.\n - setting BPM to the default value of 120.0")
            metadata['bpm'] = 120.0

        return metadata

    def _extract_field(self, content, field_name):
        """Extract a field value from .sm content"""
        pattern = f"#{field_name}:"
        start_idx = content.find(pattern)
        if start_idx == -1:
            return None

        start_idx += len(pattern)
        end_idx = content.find(';', start_idx)
        if end_idx == -1:
            return None

        value = content[start_idx:end_idx].strip()
        return value if value else None

    def _parse_steps(self, content, bpm, difficulty="beginner"):
        """Parse step data for specified difficulty"""
        difficulty_name = self.difficulties.get(difficulty)
        
        # Find the NOTES section for the specified difficulty
        target_section = self._find_notes_sections(content, difficulty_name)
        if target_section == []:
            print(f"invalid target_section for difficulty: '{difficulty}'")
            return []
        
        # Parse the step data
        steps = self._parse_step_data(target_section, bpm)
        return steps

    def _find_notes_sections(self, content, difficulty):
        """Find all NOTES sections in the content and return the section with the desired difficulty"""
        sections = []
        start_pattern = "#NOTES:"
        
        start_idx = 0
        while True:
            start_idx = content.find(start_pattern, start_idx)
            if start_idx == -1:
                break
                
            # Find the end of this section (next # or end of file)
            end_idx = content.find(';', start_idx)
            if end_idx == -1:
                end_idx = len(content)
            
            section = content[start_idx:end_idx + 1]
            sections.append(section)
            start_idx = end_idx + 1
            
        target_section = None
        for section in sections:
            if difficulty.lower() in section.lower():
                target_section = section
                break
        
        if not target_section:
            print(f"Could not find difficulty '{difficulty}' in chart")
            return []

        return target_section
    
    def _parse_step_data(self, section, bpm):
        """Parse the actual step notation into Step objects"""
        steps = []
        
        # Split section into lines and find where the step data starts
        lines = section.split('\n')
        step_data_started = False
        measure_lines = []
        current_measure = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Step data starts after the metadata lines (after the last ':')
            if ':' in line and not step_data_started:
                continue
            else:
                step_data_started = True
                
            # Check if this line contains step data (4 digits for single mode)
            if len(line) == 4 and all(c in '0123' for c in line):
                current_measure.append(line)
            elif line == ',' and current_measure:
                # End of measure
                measure_lines.append(current_measure[:])
                current_measure = []
            elif line == ';':
                # End of chart
                if current_measure:
                    measure_lines.append(current_measure[:])
                break
        
        # Convert measures to steps with timing
        ms_per_measure = (60000.0 / bpm) * 4  # 4 beats per measure at given BPM
        
        for measure_idx, measure in enumerate(measure_lines):
            measure_start_ms = measure_idx * ms_per_measure
            
            if not measure:
                continue
                
            # Each line in the measure represents a subdivision
            ms_per_line = ms_per_measure / len(measure)
            
            for line_idx, line in enumerate(measure):
                line_time_ms = measure_start_ms + (line_idx * ms_per_line)
                
                # Check each lane (Left, Down, Up, Right)
                for lane in range(4):
                    note = int(line[lane])
                    if note != 0:  # 0 means no step
                        step = Step(line_time_ms, lane, note)
                        steps.append(step)
        
        # Sort steps by time
        steps.sort(key=lambda s: s.time_ms)
        return steps

if __name__ == "__main__":
    smp = SMParser()
    smp.parse_file("src/DanceDance/7_Colors.sm")
